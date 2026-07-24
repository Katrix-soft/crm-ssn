import asyncio
import json
from mercantil_andina import MercantilAndinaClient

async def run_test():
    print("Iniciando prueba con Mercantil Andina...")
    client = MercantilAndinaClient()
    
    try:
        # 1. Probar Token
        print("\n--- 1. OBTENIENDO TOKEN ---")
        token = await client.get_token()
        print(f"Token obtenido con éxito. Inicia con: {token[:15]}...")
        
        # 2. Probar Endpoint de Productores
        print("\n--- 2. OBTENIENDO PRODUCTORES DESDE MERCANTIL ---")
        productores = await client._request("GET", "/productores/v1/")
        
        # Mostrar los primeros elementos
        if isinstance(productores, dict) and "datos" in productores:
            print(f"Se obtuvieron {productores['cantidad']} productores.")
            print("Muestra del primer productor:")
            primer_prod = productores["datos"][0]
            print(json.dumps(primer_prod, indent=2, ensure_ascii=False))
            
            # Consultar detalle si es posible
            print(f"\n--- 3. CONSULTANDO DETALLE DEL PRODUCTOR {primer_prod['cuenta']} ---")
            try:
                detalle = await client._request("GET", f"/productores/v1/{primer_prod['cuenta']}")
                print(json.dumps(detalle, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"El endpoint de detalle dio error o no existe: {e}")
        else:
            print("Respuesta:", productores)

        print("\nPruebas finalizadas. Ahí podés ver la estructura JSON para hacer el matcheo.")
        
    except Exception as e:
        print("\nOcurrió un error en la prueba:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_test())
