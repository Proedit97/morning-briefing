# 아침 브리핑

매일 아침 언론사별 뉴스를 여성 아나운서 음성으로 읽어 주는 안드로이드 앱이에요.

- **설치:** [최신 APK 내려받기](https://github.com/Proedit97/morning-briefing/releases/latest/download/morning-briefing.apk)
- **뉴스:** 매일 아침 6시 40분쯤 `data/` 폴더에 그날 브리핑이 올라와요. 기사마다 여러 매체에서 교차 확인됐는지 표시돼요.
- **음성:** 휴대폰의 Google 음성 엔진으로 읽고, 마이크로 "브리핑 시작", "다음", "MBC 뉴스", "신세계 폭발물 진짜야?"처럼 말할 수 있어요.

## 업데이트

- **화면·기능 (`www/`)**: 설치된 앱이 실행될 때 `www/index.html`의 `app-version`이 더 높으면 새 화면을 받아 바로 적용해요. 재설치가 필요 없어요. 고칠 때는 `app-version` 숫자를 올려 주세요.
- **휴대폰 쪽 기능 (`android/`)**: 바뀌면 GitHub Actions가 새 APK를 만들어 Releases에 올리고, 앱 위쪽에 '설치하기' 안내가 떠요.
