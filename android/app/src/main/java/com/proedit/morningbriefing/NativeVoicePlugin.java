package com.proedit.morningbriefing;

import android.Manifest;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

import java.util.ArrayList;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Speaks Korean text with Android's own text-to-speech engine and listens with Android's speech recognizer.
 * Each speak() call is queued (QUEUE_ADD) and resolves when that piece has been spoken, so the web layer can
 * queue the next sentences ahead and playback never stalls between stories.
 */
@CapacitorPlugin(
    name = "NativeVoice",
    permissions = { @Permission(alias = "microphone", strings = { Manifest.permission.RECORD_AUDIO }) }
)
public class NativeVoicePlugin extends Plugin {

    private TextToSpeech tts;
    private volatile boolean ttsReady = false;
    private final ArrayList<PluginCall> waitingForReady = new ArrayList<>();
    private final Map<String, PluginCall> pending = new ConcurrentHashMap<>();
    private SpeechRecognizer recognizer;
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    public void load() {
        tts = new TextToSpeech(getContext(), status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(Locale.KOREAN);
                ttsReady = true;
            }
            synchronized (waitingForReady) {
                for (PluginCall c : waitingForReady) {
                    if (ttsReady) c.resolve(voicesResult()); else c.reject("이 기기에서 음성 읽기를 시작하지 못했어요.", "no_tts");
                }
                waitingForReady.clear();
            }
        });
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) {
                JSObject o = new JSObject(); o.put("id", id); notifyListeners("ttsStart", o);
            }
            @Override public void onDone(String id) {
                PluginCall c = pending.remove(id);
                if (c != null) { c.resolve(); c.release(bridge); }
            }
            @Override public void onError(String id) { fail(id, "error"); }
            @Override public void onError(String id, int code) { fail(id, "error"); }
            @Override public void onStop(String id, boolean interrupted) { fail(id, "interrupted"); }
        });
    }

    private void fail(String id, String code) {
        PluginCall c = pending.remove(id);
        if (c != null) { c.reject(code, code); c.release(bridge); }
    }

    private JSObject voicesResult() {
        JSArray arr = new JSArray();
        try {
            if (tts.getVoices() != null) {
                for (Voice v : tts.getVoices()) {
                    Locale l = v.getLocale();
                    if (l == null || !"ko".equals(l.getLanguage())) continue;
                    JSObject o = new JSObject();
                    o.put("name", v.getName());
                    o.put("quality", v.getQuality());
                    o.put("network", v.isNetworkConnectionRequired());
                    o.put("installed", !v.getFeatures().contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED));
                    arr.put(o);
                }
            }
        } catch (Exception ignored) { }
        JSObject r = new JSObject();
        r.put("voices", arr);
        r.put("engine", tts.getDefaultEngine());
        return r;
    }

    @PluginMethod
    public void getVoices(PluginCall call) {
        if (ttsReady) { call.resolve(voicesResult()); return; }
        synchronized (waitingForReady) { waitingForReady.add(call); }
    }

    @PluginMethod
    public void speak(PluginCall call) {
        if (!ttsReady) { call.reject("음성 엔진이 아직 준비되지 않았어요.", "not_ready"); return; }
        String text = call.getString("text", "");
        String id = call.getString("id", String.valueOf(System.nanoTime()));
        float rate = call.getFloat("rate", 1.0f);
        float pitch = call.getFloat("pitch", 1.0f);
        String voiceName = call.getString("voice", null);
        boolean flush = Boolean.TRUE.equals(call.getBoolean("flush", false));
        if (voiceName != null && tts.getVoices() != null) {
            for (Voice v : tts.getVoices()) {
                if (v.getName().equals(voiceName)) { tts.setVoice(v); break; }
            }
        } else {
            tts.setLanguage(Locale.KOREAN);
        }
        tts.setSpeechRate(rate);
        tts.setPitch(pitch);
        call.setKeepAlive(true);
        pending.put(id, call);
        Bundle params = new Bundle();
        int res = tts.speak(text, flush ? TextToSpeech.QUEUE_FLUSH : TextToSpeech.QUEUE_ADD, params, id);
        if (res == TextToSpeech.ERROR) { pending.remove(id); call.setKeepAlive(false); call.reject("읽기에 실패했어요.", "error"); }
    }

    @PluginMethod
    public void stop(PluginCall call) {
        if (tts != null) tts.stop();
        for (String id : new ArrayList<>(pending.keySet())) fail(id, "interrupted");
        call.resolve();
    }

    /* ---------------- speech recognition ---------------- */

    @PluginMethod
    public void startListening(PluginCall call) {
        if (getPermissionState("microphone") != PermissionState.GRANTED) {
            requestPermissionForAlias("microphone", call, "micPermission");
            return;
        }
        beginListening(call);
    }

    @PermissionCallback
    private void micPermission(PluginCall call) {
        if (getPermissionState("microphone") == PermissionState.GRANTED) beginListening(call);
        else call.reject("마이크 권한이 없어요.", "not_granted");
    }

    private void beginListening(PluginCall call) {
        if (!SpeechRecognizer.isRecognitionAvailable(getContext())) { call.reject("이 기기에서 음성 인식을 쓸 수 없어요.", "unavailable"); return; }
        main.post(() -> {
            if (recognizer != null) { recognizer.destroy(); }
            recognizer = SpeechRecognizer.createSpeechRecognizer(getContext());
            recognizer.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle b) { state("listening", null); }
                @Override public void onBeginningOfSpeech() { }
                @Override public void onRmsChanged(float v) { }
                @Override public void onBufferReceived(byte[] bytes) { }
                @Override public void onEndOfSpeech() { }
                @Override public void onError(int err) { state("idle", err == SpeechRecognizer.ERROR_NO_MATCH || err == SpeechRecognizer.ERROR_SPEECH_TIMEOUT ? "no_speech" : "error"); }
                @Override public void onResults(Bundle b) {
                    ArrayList<String> r = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    JSObject o = new JSObject(); o.put("text", r != null && !r.isEmpty() ? r.get(0) : "");
                    notifyListeners("final", o);
                    state("idle", "done");
                }
                @Override public void onPartialResults(Bundle b) {
                    ArrayList<String> r = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (r != null && !r.isEmpty()) { JSObject o = new JSObject(); o.put("text", r.get(0)); notifyListeners("partial", o); }
                }
                @Override public void onEvent(int i, Bundle b) { }
            });
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ko-KR");
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
            recognizer.startListening(intent);
            call.resolve();
        });
    }

    @PluginMethod
    public void stopListening(PluginCall call) {
        main.post(() -> { if (recognizer != null) recognizer.stopListening(); call.resolve(); });
    }

    private void state(String s, String reason) {
        JSObject o = new JSObject(); o.put("state", s); if (reason != null) o.put("reason", reason);
        notifyListeners("listenState", o);
    }

    @Override
    protected void handleOnDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        main.post(() -> { if (recognizer != null) recognizer.destroy(); });
    }
}
