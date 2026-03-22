import asyncio
import httpx

async def main():
    print("Iniciando requisicao de captura direto no Gateway...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Pega a senha e auth do Gateway via Biometrics
        try:
            res = await client.post(
                "http://10.11.0.4:9500/gateway/capture-fingerprint",
                json={
                    "dev_index": "17b00d62-e439-4b7b-a464-e4c1159d44e5", 
                    "finger_no": 1
                }
            )
            print("Status Code:", res.status_code)
            print("Response JSON:")
            print(res.text)
        except Exception as e:
            print("Error:", str(e))

asyncio.run(main())
