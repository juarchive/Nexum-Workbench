# Nexum Android — prévia em desenvolvimento

Autoria do Nexum: Davi P. Souza.

Esta implementação compartilha as 43 calculadoras Python com o desktop, com navegação por tarefa, instruções, formulários, desenvolvimento do cálculo, gráficos e um caderno local de registros JSON. Não requer servidor nem permissão de internet. Os registros não usam o formato de projeto `.nexum7`; são evidências de cálculo exportáveis.

**Não equivale ao aplicativo desktop completo.** Visualização molecular 3D, bancadas animadas, importação de séries e laboratório completo ainda precisam de implementação móvel. A compilação local de `assembleDebug`, `assembleDebugAndroidTest` e `lintDebug` passou (zero erros de lint, seis avisos). A assinatura debug foi verificada com apksigner. A interface Android ainda precisa de inspeção visual e testes em dispositivo físico. O fundo usa gradiente e cartões translúcidos; não representa ainda a paisagem aprovada no desktop.

## Compilar

Requer JDK 17, Gradle 8.9, Android SDK 35 e Python 3.12. Abra a pasta `android` no Android Studio ou execute na raiz:

```sh
gradle -p android assembleDebug lintDebug
gradle -p android connectedDebugAndroidTest
```

O APK de teste fica em `android/app/build/outputs/apk/debug/app-debug.apk`. A compilação inicial precisa baixar dependências. O APK inclui o motor Python por Chaquopy e funciona offline. A configuração é Android 7/API 24 ou superior, arm64 e x86_64.

Referências de configuração: https://chaquo.com/chaquopy/doc/current/android.html e https://developer.android.com/build/releases/agp-8-7-0-release-notes .

## Releases e assinatura

O workflow `Android APK` compila e executa testes do motor dentro de emulador. Em branches/PRs, disponibiliza APK **debug** como artefato de teste, não como release de produção. Tags `android-v*` também exigem assinatura de distribuição e publicam uma **pré-release** com APK e SHA-256, somente se as etapas anteriores passarem.

Configurar no GitHub Actions: `NEXUM_ANDROID_KEYSTORE_BASE64`, `NEXUM_ANDROID_STORE_PASSWORD`, `NEXUM_ANDROID_KEY_ALIAS`, `NEXUM_ANDROID_KEY_PASSWORD`. A chave pertence ao responsável pela distribuição e deve ser preservada para permitir atualizações. Não armazenar chave nem senhas no repositório. Sem esses dados, o build de release falha explicitamente; não utiliza a chave debug como substituta.

Antes de cada release, incrementar `versionCode` e `versionName` em `android/app/build.gradle`, testar instalação e atualização e revisar a cobertura real. Não publicar uma versão estável enquanto houver funcionalidades prometidas ausentes.
