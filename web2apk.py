import os
import shutil
import subprocess
import time
from pathlib import Path

# 🎯 Personalização
APP_NAME = "WebToAPK"
PACKAGE_NAME = "com.borge.web2apk"
INDEX_FILE = "index.html"
BUILD_FOLDER = "apkbuild"
USE_LEGACY = True  # ✅ ativa suporte a build-tools 25.0.3

# 🌈 CLI moderna com Rich
try:
    from rich import print
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("🔧 Instalando dependências...")
    os.system("pip install rich")
    from rich import print
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def criar_estrutura_android(output_path):
    console.print("[cyan]📁 Gerando estrutura Android...[/cyan]")
    Path(f"{output_path}/app/src/main/assets").mkdir(parents=True, exist_ok=True)
    Path(f"{output_path}/app/src/main/java/{PACKAGE_NAME.replace('.', '/')}").mkdir(parents=True, exist_ok=True)

    # AndroidManifest.xml
    with open(f"{output_path}/app/src/main/AndroidManifest.xml", "w") as f:
        f.write(f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="{APP_NAME}" android:theme="@android:style/Theme.NoTitleBar">
        <activity android:name=".MainActivity"
                  android:configChanges="orientation|keyboardHidden|screenSize"
                  android:label="{APP_NAME}"
                  android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>''')

    # MainActivity.java
    with open(f"{output_path}/app/src/main/java/{PACKAGE_NAME.replace('.', '/')}/MainActivity.java", "w") as f:
        f.write(f'''package {PACKAGE_NAME};

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;

public class MainActivity extends Activity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.loadUrl("file:///android_asset/{INDEX_FILE}");
        setContentView(webView);
    }}
}}''')

    # build.gradle (app)
    build_tools_version = "25.0.3" if USE_LEGACY else "33.0.2"
    compile_sdk = 25 if USE_LEGACY else 33

    with open(f"{output_path}/app/build.gradle", "w") as f:
        f.write(f'''apply plugin: 'com.android.application'

android {{
    namespace "{PACKAGE_NAME}"
    compileSdkVersion {compile_sdk}
    buildToolsVersion "{build_tools_version}"
    defaultConfig {{
        applicationId "{PACKAGE_NAME}"
        minSdkVersion 16
        targetSdkVersion {compile_sdk}
        versionCode 1
        versionName "1.0"
    }}
    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }}
    }}
}}

dependencies {{}}''')

    # build.gradle (root)
    gradle_version = "3.3.0" if USE_LEGACY else "8.2.0"
    with open(f"{output_path}/build.gradle", "w") as f:
        f.write(f'''buildscript {{
    repositories {{
        google()
        mavenCentral()
    }}
    dependencies {{
        classpath 'com.android.tools.build:gradle:{gradle_version}'
    }}
}}
allprojects {{
    repositories {{
        google()
        mavenCentral()
    }}
}}''')

    # settings.gradle
    with open(f"{output_path}/settings.gradle", "w") as f:
        f.write("include ':app'")

def copiar_site(site_path, output_path):
    console.print(f"[green]📦 Copiando site: [bold]{site_path}[/bold][/green]")
    assets_path = Path(output_path) / "app/src/main/assets"
    for item in os.listdir(site_path):
        src = os.path.join(site_path, item)
        dst = os.path.join(assets_path, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

def configurar_sdk_local(output_path):
    sdk_path = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/android-sdk")
    if not Path(sdk_path).exists():
        print(f"[red]❌ SDK Android não encontrado em {sdk_path}[/red]")
        return False
    with open(Path(output_path) / "local.properties", "w") as f:
        f.write(f"sdk.dir={sdk_path}")
    return True

def compilar_apk(output_path):
    console.print("[yellow]⚙️ Iniciando compilação...[/yellow]")

    gradle_bin = shutil.which("gradle") or "/data/data/com.termux/files/home/gradle-8.2.1/bin/gradle"
    if not Path(gradle_bin).exists():
        console.print("[red]❌ Gradle não encontrado[/red]")
        return

    if not configurar_sdk_local(output_path):
        return

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            progress.add_task(description="Compilando APK...", total=None)
            subprocess.run(f"cd {output_path} && {gradle_bin} build", shell=True, check=True)
        console.print("[bold green]✅ APK gerado com sucesso![/bold green]")
    except subprocess.CalledProcessError as e:
        console.print("[bold red]❌ Falha na compilação[/bold red]")
        console.print("🔎 Dica: AAPT2 pode não funcionar em sistemas 32-bit (Termux)")
        console.print("👉 Tente ativar o modo legacy ou compilar fora do Termux")
        console.print(f"[dim]Erro técnico: {e}[/dim]")

def main():
    print("[bold blue]\n🌐 Web2APK - Transforme seu site HTML em um app Android![/bold blue]")
    site_path = Prompt.ask("📂 Caminho da pasta do site (HTML/CSS/JS)").strip()
    output_path = os.path.abspath(BUILD_FOLDER)

    if not Path(site_path).exists():
        print("[red]❌ Caminho inválido[/red]")
        return

    if Path(output_path).exists():
        shutil.rmtree(output_path)

    start = time.time()
    criar_estrutura_android(output_path)
    copiar_site(site_path, output_path)
    compilar_apk(output_path)
    duracao = round(time.time() - start, 2)

    apk_path = Path(output_path) / "app/build/outputs/apk/debug/app-debug.apk"
    if apk_path.exists():
        console.print(f"[bold green]🎉 APK pronto: [yellow]{apk_path}[/yellow][/bold green]")
        console.print(f"[dim]⏱ Tempo total: {duracao} segundos[/dim]")
    else:
        console.print("[red]⚠️ APK não encontrado. Verifique os logs de erro[/red]")

if __name__ == "__main__":
    main()