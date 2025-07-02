from core.core import criar_chat
import asyncio

async def main():
    chat = criar_chat()
    print("🧠 Chat IA iniciado! Pergunte algo (ou digite 'sair' para encerrar)")

    while True:
        pergunta = input("\nVocê: ")

        if pergunta.strip().lower() in ["sair", "exit", "quit"]:
            print("👋 Encerrando... Até logo!")
            break

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, chat.send_message, pergunta)
            resposta = response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            resposta = f"Desculpa, houve um erro técnico: {e}"

        # Imprime a resposta em partes, se for longa
        if len(resposta) <= 600:
            print(f"\n🤖 IA: {resposta}")
        else:
            parts = [resposta[i : i + 600] for i in range(0, len(resposta), 600)]
            print("\n🤖 IA:")
            for part in parts:
                print(part)

        # Verifica se a IA está se despedindo
        if "adeus" in resposta.lower() or "tchau" in resposta.lower():
            print("\n👋 A IA se despediu. Encerrando o chat.")
            break

if __name__ == '__main__':
    asyncio.run(main())