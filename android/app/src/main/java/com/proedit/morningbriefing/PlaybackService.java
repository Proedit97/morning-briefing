package com.proedit.morningbriefing;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;

import androidx.core.app.NotificationCompat;

/**
 * Keeps the briefing reading while the screen is off or another app is open.
 * Android stops background apps from running; a "media playback" foreground service with a
 * notification (with a 멈추기 button) is the supported way to keep speaking.
 */
public class PlaybackService extends Service {

    static final String ACTION_STOP = "com.proedit.morningbriefing.STOP";
    static final String EXTRA_TEXT = "text";
    private static final String CHANNEL = "briefing_playback";
    private static final int NOTIFY_ID = 7301;

    private PowerManager.WakeLock wakeLock;

    static void start(Context ctx, String text) {
        Intent i = new Intent(ctx, PlaybackService.class);
        i.putExtra(EXTRA_TEXT, text);
        try {
            if (Build.VERSION.SDK_INT >= 26) ctx.startForegroundService(i); else ctx.startService(i);
        } catch (Exception ignored) { }
    }

    /** Show which story is being read, without restarting the service. */
    static void update(Context ctx, String text) {
        try {
            NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            PlaybackService s = running;
            if (nm != null && s != null) nm.notify(NOTIFY_ID, s.build(text));
        } catch (Exception ignored) { }
    }

    private static PlaybackService running;

    static void stop(Context ctx) {
        try { ctx.stopService(new Intent(ctx, PlaybackService.class)); } catch (Exception ignored) { }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            NativeVoicePlugin.stopFromNotification();
            stopForegroundCompat();
            stopSelf();
            return START_NOT_STICKY;
        }
        String text = intent != null ? intent.getStringExtra(EXTRA_TEXT) : null;
        running = this;
        Notification n = build(text != null ? text : "브리핑을 읽고 있어요");
        try {
            if (Build.VERSION.SDK_INT >= 29) startForeground(NOTIFY_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
            else startForeground(NOTIFY_ID, n);
        } catch (Exception e) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (wakeLock == null) {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (pm != null) {
                wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "morningbriefing:playback");
                wakeLock.setReferenceCounted(false);
            }
        }
        if (wakeLock != null) wakeLock.acquire(60 * 60 * 1000L);   // a full briefing is well under an hour
        return START_NOT_STICKY;
    }

    private Notification build(String text) {
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26 && nm != null && nm.getNotificationChannel(CHANNEL) == null) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "브리핑 재생", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("화면이 꺼져도 브리핑을 계속 읽을 때 표시돼요");
            ch.setShowBadge(false);
            nm.createNotificationChannel(ch);
        }
        int immutable = Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0;
        Intent open = new Intent(this, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent openPi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | immutable);
        Intent stop = new Intent(this, PlaybackService.class).setAction(ACTION_STOP);
        PendingIntent stopPi = PendingIntent.getService(this, 1, stop, PendingIntent.FLAG_UPDATE_CURRENT | immutable);
        return new NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentTitle("아침 브리핑")
            .setContentText(text)
            .setContentIntent(openPi)
            .addAction(android.R.drawable.ic_media_pause, "멈추기", stopPi)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setCategory(NotificationCompat.CATEGORY_TRANSPORT)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build();
    }

    private void stopForegroundCompat() {
        try {
            if (Build.VERSION.SDK_INT >= 24) stopForeground(STOP_FOREGROUND_REMOVE); else stopForeground(true);
        } catch (Exception ignored) { }
    }

    @Override
    public void onDestroy() {
        if (running == this) running = null;
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        stopForegroundCompat();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
