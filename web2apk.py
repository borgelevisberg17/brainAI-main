import os
import sys
import shutil
import subprocess
import zipfile
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PACKAGE_NAME = "com.borge.brainai"
BUILD_FOLDER = Path("apkbuild")
TOOLS_FOLDER = Path("env_tools")

# Links oficiais das ferramentas para Windows
JDK_URL = "https://download.oracle.com/java/17/archive/jdk-17.0.10_windows-x64_bin.zip"
SDK_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
GRADLE_URL = "https://services.gradle.org/distributions/gradle-8.4-bin.zip"

def baixar_e_extrair(url, destino_zip, pasta_extracao):
    """Auxiliar para baixar arquivos grandes com barra de progresso simples."""
    if not pasta_extracao.exists():
        pasta_extracao.mkdir(parents=True, exist_ok=True)
        print(f"📥 Baixando: {url}")
        
        def progresso(count, block_size, total_size):
            porcentagem = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rProgresso: {porcentagem}%")
            sys.stdout.flush()
            
        urllib.request.urlretrieve(url, destino_zip, reporthook=progresso)
        print(f"\n📦 Extraindo em {pasta_extracao}...")
        with zipfile.ZipFile(destino_zip, 'r') as zip_ref:
            zip_ref.extractall(pasta_extracao)
        os.remove(destino_zip)
    else:
        print(f"✅ Componente já existe em: {pasta_extracao}")

def garantir_ambiente_windows():
    """Verifica a consistência do ambiente. Se algo faltar, baixa localmente."""
    print("🔍 Verificando consistência do ambiente...")
    TOOLS_FOLDER.mkdir(exist_ok=True)
    
    # 1. VERIFICAÇÃO / INSTALAÇÃO DO JDK 17
    if not os.environ.get("JAVA_HOME"):
        jdk_local = TOOLS_FOLDER / "jdk-17.0.10"
        if not jdk_local.exists():
            print("❌ JAVA_HOME não detectado.")
            baixar_e_extrair(JDK_URL, TOOLS_FOLDER / "jdk.zip", TOOLS_FOLDER)
        # O zip da Oracle extrai uma pasta interna chamada 'jdk-17.0.10'
        os.environ["JAVA_HOME"] = str(jdk_local.resolve())
        print(f"☕ JAVA_HOME definido localmente: {os.environ['JAVA_HOME']}")
    
    # 2. VERIFICAÇÃO / INSTALAÇÃO DO ANDROID SDK
    if not os.environ.get("ANDROID_HOME"):
        # Tenta o caminho padrão do Android Studio primeiro
        default_sdk = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
        if default_sdk.exists():
            os.environ["ANDROID_HOME"] = str(default_sdk)
        else:
            sdk_local = TOOLS_FOLDER / "android-sdk"
            cmdline_tools_path = sdk_local / "cmdline-tools" / "latest" / "bin"
            
            if not cmdline_tools_path.exists():
                print("❌ Android SDK não detectado.")
                # O Cmdline-tools precisa de uma estrutura de pastas específica para funcionar no Windows
                temp_extract = TOOLS_FOLDER / "sdk_temp"
                baixar_e_extrair(SDK_TOOLS_URL, TOOLS_FOLDER / "sdk_tools.zip", temp_extract)
                
                (sdk_local / "cmdline-tools").mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_extract / "cmdline-tools"), str(sdk_local / "cmdline-tools" / "latest"))
                shutil.rmtree(temp_extract)
                
            os.environ["ANDROID_HOME"] = str(sdk_local.resolve())
            
    print(f"🤖 ANDROID_HOME definido em: {os.environ['ANDROID_HOME']}")

    # 3. VERIFICAÇÃO / INSTALAÇÃO DO GRADLE
    gradle_local = TOOLS_FOLDER / "gradle-8.4"
    if not gradle_local.exists():
        print("❌ Gradle não detectado.")
        baixar_e_extrair(GRADLE_URL, TOOLS_FOLDER / "gradle.zip", TOOLS_FOLDER)

    # 4. ATUALIZAR PATH EM TEMPO DE EXECUÇÃO
    # Adiciona os binários locais ao PATH do processo atual do Python
    bin_paths = [
        Path(os.environ["JAVA_HOME"]) / "bin",
        Path(os.environ["ANDROID_HOME"]) / "cmdline-tools" / "latest" / "bin",
        Path(os.environ["ANDROID_HOME"]) / "platform-tools",
        gradle_local / "bin"
    ]
    
    for path in bin_paths:
        path_str = str(path.resolve())
        if path_str not in os.environ["PATH"]:
            os.environ["PATH"] = path_str + os.pathsep + os.environ["PATH"]

    # 5. ACEITAR LICENÇAS E INSTALAR PLATAFORMAS (Se necessário)
    print("🔏 Aceitando licenças do Android SDK e instalando Build Tools 34...")
    try:
        # No Windows, passamos o echo "y" usando o shell do subprocess
        sdk_manager = shutil.which("sdkmanager")
        if not sdk_manager:
            raise FileNotFoundError("sdkmanager não encontrado no PATH gerado.")
            
        process = subprocess.Popen(
            f'echo y | "{sdk_manager}" --sdk_root="{os.environ["ANDROID_HOME"]}" "platforms;android-34" "build-tools;34.0.0" "platform-tools"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process.communicate()
        print("✅ Licenças aceitas e dependências do Android prontas!")
    except Exception as e:
        print(f"⚠️ Alerta ao configurar licenças: {e}. Se o build falhar, execute o sdkmanager manualmente.")

def importar_site():
    print("\n🌐 Escolha uma opção para fornecer o site:")
    print("1 - Informar caminho do arquivo .zip")
    print("2 - Colar o código HTML diretamente")

    opcao = input("Digite o número da opção: ").strip()
    frontend_dir = Path("frontend")
    frontend_dir.mkdir(exist_ok=True)

    if opcao == "1":
        path = input("Digite o caminho completo para o arquivo .zip: ").strip().strip('"')
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(frontend_dir)
    elif opcao == "2":
        html_code = []
        print("🧾 Cole seu código HTML (digite 'FIM' numa nova linha para finalizar):")
        while True:
            linha = input()
            if linha.strip().upper() == "FIM":
                break
            html_code.append(linha)
        with open(frontend_dir / "index.html", "w", encoding="utf-8") as f:
            f.write("\n".join(html_code))
    else:
        raise ValueError("❌ Opção inválida!")

    index_candidates = list(frontend_dir.rglob("index.html"))
    if not index_candidates:
        raise FileNotFoundError("❌ index.html não encontrado na pasta extraída.")
    
    relative_path = index_candidates[0].relative_to(frontend_dir)
    print(f"✅ index.html localizado em: frontend/{relative_path}")
    return relative_path.as_posix()

def gerar_icones():
    print("🎨 Gerando ícones...")
    sizes = {"mipmap-mdpi": 48, "mipmap-hdpi": 72, "mipmap-xhdpi": 96, "mipmap-xxhdpi": 144, "mipmap-xxxhdpi": 192}
    font = ImageFont.load_default()
    for folder, size in sizes.items():
        img = Image.new("RGBA", (size, size), "#0d0d0d")
        draw = ImageDraw.Draw(img)
        draw.text((size // 4, size // 4), "🤖", fill="white", font=font)
        out_path = BUILD_FOLDER / "app" / "src" / "main" / "res" / folder
        out_path.mkdir(parents=True, exist_ok=True)
        img.save(out_path / "ic_launcher.png")

def gerar_splash(app_name):
    print("🚀 Gerando splash screen...")
    drawable_dir = BUILD_FOLDER / "app" / "src" / "main" / "res" / "drawable"
    drawable_dir.mkdir(parents=True, exist_ok=True)
    splash = Image.new("RGBA", (720, 1280), "#000000")
    draw = ImageDraw.Draw(splash)
    font = ImageFont.load_default()
    draw.text((280, 600), app_name, fill="white", font=font)
    splash_path = drawable_dir / "splash.png"
    splash.save(splash_path)

def criar_projeto_android(index_path, app_name):
    print("📁 Criando estrutura do projeto Android...")
    java_dir = BUILD_FOLDER / "app" / "src" / "main" / "java" / PACKAGE_NAME.replace('.', '/')
    assets_dir = BUILD_FOLDER / "app" / "src" / "main" / "assets"
    layout_dir = BUILD_FOLDER / "app" / "src" / "main" / "res" / "layout"
    
    java_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    layout_dir.mkdir(parents=True, exist_ok=True)

    sdk_path_escaped = os.environ['ANDROID_HOME'].replace('\\', '\\\\')

    (BUILD_FOLDER / "settings.gradle").write_text("include ':app'", encoding="utf-8")
    (BUILD_FOLDER / "local.properties").write_text(f"sdk.dir={sdk_path_escaped}", encoding="utf-8")
    (BUILD_FOLDER / "gradle.properties").write_text("android.useAndroidX=true\nandroid.enableJetifier=true", encoding="utf-8")

    (BUILD_FOLDER / "app" / "src" / "main" / "AndroidManifest.xml").write_text(f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{PACKAGE_NAME}">
    <uses-permission android:name="android.permission.INTERNET" />
    <application android:label="{app_name}" android:icon="@mipmap/ic_launcher" android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity android:name=".SplashActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <activity android:name=".MainActivity" android:exported="false"></activity>
    </application>
</manifest>""", encoding="utf-8")

    (java_dir / "MainActivity.java").write_text(f"""package {PACKAGE_NAME};
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public class MainActivity extends Activity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("file:///android_asset/{index_path}");
        setContentView(webView);
    }}
}}""", encoding="utf-8")

    (java_dir / "SplashActivity.java").write_text(f"""package {PACKAGE_NAME};
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
public class SplashActivity extends Activity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.style.Theme_AppCompat_Light_NoActionBar == 0 ? 0 : R.layout.activity_splash);
        new Handler(Looper.getMainLooper()).postDelayed(() -> {{
            Intent intent = new Intent(SplashActivity.this, MainActivity.class);
            startActivity(intent);
            finish();
        }}, 3000);
    }}
}}""", encoding="utf-8")

    (layout_dir / "activity_splash.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_width="match_parent" android:layout_height="match_parent" android:background="@android:color/black">
    <ImageView android:layout_width="match_parent" android:layout_height="match_parent" android:scaleType="centerCrop" android:src="@drawable/splash" />
</RelativeLayout>""", encoding="utf-8")

    (BUILD_FOLDER / "build.gradle").write_text("""buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.2.0' }
}
allprojects { repositories { google(); mavenCentral() } }""", encoding="utf-8")

    (BUILD_FOLDER / "app" / "build.gradle").write_text(f"""plugins {{ id 'com.android.application' }}
android {{
    namespace '{PACKAGE_NAME}'
    compileSdk 34
    defaultConfig {{ applicationId '{PACKAGE_NAME}'; minSdk 21; targetSdk 34; versionCode 1; versionName "1.0" }}
    buildTypes {{ release {{ minifyEnabled false }} }}
}}
dependencies {{ implementation 'androidx.appcompat:appcompat:1.6.1' }}""", encoding="utf-8")

def copiar_site_para_assets():
    src = Path("frontend")
    dst = BUILD_FOLDER / "app" / "src" / "main" / "assets"
    if dst.exists(): shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        target = dst / item.relative_to(src)
        if item.is_dir(): target.mkdir(parents=True, exist_ok=True)
        else: shutil.copy2(item, target)

def compilar_apk():
    print("⚙️ Compilando APK...")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    apk_path = BUILD_FOLDER / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    
    try:
        cmd_clean = f"cd {BUILD_FOLDER} && gradle clean"
        cmd_build = f"cd {BUILD_FOLDER} && gradle assembleDebug"
        
        subprocess.run(cmd_clean, shell=True, check=True)
        result = subprocess.run(cmd_build, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Erro ao compilar o APK.\n")
            print(result.stderr)
        elif apk_path.exists():
            final_apk = output_dir / "app-debug.apk"
            shutil.copy(apk_path, final_apk)
            print(f"\n🎯 APK GERADO COM SUCESSO!\n📂 Arquivo disponível em: {final_apk.resolve()}")
    except Exception as e:
        print(f"❌ Falha crítica ao executar compilação do Gradle: {e}")

def run_windows_builder():
    start = time.time()
    app_name = input("📛 Digite o nome do aplicativo: ").strip()
    if not app_name:
        raise ValueError("❌ O nome do aplicativo não pode estar vazio!")

    garantir_ambiente_windows()
    index_path = importar_site()
    criar_projeto_android(index_path, app_name)
    gerar_icones()
    gerar_splash(app_name)
    copiar_site_para_assets()
    compilar_apk()
    print(f"⏱️ Processo completo finalizado em {round(time.time() - start, 2)} segundos")

if __name__ == "__main__":
    run_windows_builder()