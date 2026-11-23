// Pretend Android: answers the bridge like the real NativeVoicePlugin would.
window.__calls = []; window.__listeners = {};
window.androidBridge = {
  postMessage(json) {
    const m = JSON.parse(json);
    if (m.type === "message" || m.callbackId) {
      window.__calls.push(m.pluginId + "." + m.methodName);
      const reply = (data) => setTimeout(() => window.Capacitor.fromNative({callbackId: m.callbackId, pluginId: m.pluginId, methodName: m.methodName, success: true, data, save: m.methodName === "addListener"}), 5);
      if (m.pluginId !== "NativeVoice") return reply({});
      switch (m.methodName) {
        case "addListener": window.__listeners[m.options.eventName] = m.callbackId; break;
        case "getVoices": setTimeout(() => reply({voices: [{name: "ko-kr-x-ism-local", installed: true}, {name: "ko-kr-x-koc-local", installed: true}]}), 1500); break; // slow engine
        case "getAppInfo": reply({versionName: "1.0.6", versionCode: 6}); break;
        case "getLaunch": reply({}); break;
        case "speak":
          const fire = window.__listeners.ttsStart;
          if (fire) setTimeout(() => window.Capacitor.fromNative({callbackId: fire, pluginId: "NativeVoice", methodName: "addListener", success: true, data: {id: m.options.id}, save: true}), 2);
          setTimeout(() => reply({}), 20); break;
        case "speakQueue": {
          window.__queued = m.options.items.map(x => x.id);
          const ev = (name, data) => { const cb = window.__listeners[name]; if (cb) window.Capacitor.fromNative({callbackId: cb, pluginId: "NativeVoice", methodName: "addListener", success: true, data, save: true}); };
          let t = 5; window.__qtimers = [];
          m.options.items.forEach(x => { window.__qtimers.push(setTimeout(() => ev("ttsStart", {id: x.id}), t)); t += 3; window.__qtimers.push(setTimeout(() => ev("ttsDone", {id: x.id}), t)); });
          reply({last: m.options.items[m.options.items.length - 1].id}); break; }
        case "stop": (window.__qtimers || []).forEach(clearTimeout); reply({}); break;
        default: reply({});
      }
    }
  }
};
window.Capacitor = { PluginHeaders: [{name: "NativeVoice", methods: ["addListener","removeListener","removeAllListeners","getVoices","speak","speakQueue","requestNotifications","stop","getLaunch","getAppInfo","startListening","stopListening"].map(n => ({name: n, rtype: n === "addListener" ? "callback" : "promise"}))}] };
