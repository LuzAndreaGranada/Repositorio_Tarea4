import happybase 
import pandas as pd

try:
    # Conectar con HBase
    connection = happybase.Connection('localhost')
    print("Conexión con HBase establecida.")

    # Crear tabla y familias de columnas
    table_name = 'tienda_virtual_armenia'
    families = {
        'entidad': dict(),
        'orden': dict(),
        'proveedor': dict(),
        'detalle': dict()
    }

    if table_name.encode() in connection.tables():
        print(f"Eliminando tabla existente: {table_name}")
        connection.delete_table(table_name, disable=True)

    connection.create_table(table_name, families)
    table = connection.table(table_name)
    print(f"Tabla '{table_name}' creada correctamente.")

    # Leer dataset desde la URL
    url = "https://www.datos.gov.co/resource/qc6t-5eda.csv"
    df = pd.read_csv(url)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    print("Columnas detectadas:", df.columns.tolist())

    # Validar que 'total' esté presente
    if 'total' not in df.columns:
        raise ValueError("La columna 'total' no se encontró en el dataset.")

    # Limpieza de datos
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)

    for col in df.select_dtypes(include='number').columns:
        df[col] = df[col].fillna(0)

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].fillna('')

    # Cargar en HBase
    for idx, row in df.iterrows():
        row_key = f"orden_{idx}".encode()
        data = {
            b'entidad:a_o': str(row.get('a_o', '')).encode(),
            b'entidad:nit': str(row.get('nit_entidad', '')).encode(),
            b'entidad:entidad': str(row.get('entidad', '')).encode(),
            b'entidad:sector': str(row.get('sector_de_la_entidad', '')).encode(),
            b'entidad:rama': str(row.get('rama_de_la_entidad', '')).encode(),

            b'orden:id': str(row.get('identificador_de_la_orden', '')).encode(),
            b'orden:fecha': str(row.get('fecha', '')).encode(),
            b'orden:estado': str(row.get('estado', '')).encode(),
            b'orden:items': str(row.get('items', '')).encode(),
            b'orden:total': str(row.get('total', '')).encode(),

            b'proveedor:nombre': str(row.get('proveedor', '')).encode(),
            b'proveedor:solicitante': str(row.get('solicitante', '')).encode(),

            b'detalle:ciudad': str(row.get('ciudad', '')).encode(),
            b'detalle:agregacion': str(row.get('agregacion', '')).encode(),
            b'detalle:postconflicto': str(row.get('espostconflicto', '')).encode(),
            b'detalle:entidad_obligada': str(row.get('entidad_obligada', '')).encode()
        }
        table.put(row_key, data)

    print("Datos cargados exitosamente en HBase.")

    # Consultar las primeras 5 órdenes
    print("\n=== Primeras 5 órdenes ===")
    count = 0
    for key, data in table.scan():
        if count < 5:
            print(f"\n Orden ID: {key.decode()}")
            print(f" Entidad: {data.get(b'entidad:entidad', b'').decode()}")
            print(f" Proveedor: {data.get(b'proveedor:nombre', b'').decode()}")
            print(f" Items: {data.get(b'orden:items', b'').decode()}")
            print(f" Total: {data.get(b'orden:total', b'').decode()}")
            count += 1
        else:
            break

    # === CONSULTAS DE SELECCIÓN Y OPERACIONES ===

    print("\n=== Filtrar órdenes con total > 100 millones ===")
    for key, data in table.scan():
        total = float(data.get(b'orden:total', b'0').decode())
        if total > 100_000_000:
            print(f"\n Orden: {key.decode()} - Total: {total}")

    print("\n=== Insertar nueva orden ===")
    new_key = b'orden_nueva'
    new_data = {
        b'entidad:entidad': b'Nueva Entidad',
        b'orden:id': b'99999999',
        b'orden:fecha': b'2025-05-01',
        b'orden:total': b'12345678',
        b'proveedor:nombre': b'Proveedor XYZ'
    }
    table.put(new_key, new_data)
    print(f"Orden insertada con key: {new_key.decode()}")

    print("\n=== Actualizar total de una orden existente ===")
    update_key = b'orden_1'
    table.put(update_key, {b'orden:total': b'99999999'})
    print(f"Orden {update_key.decode()} actualizada.")

    print("\n=== Eliminar orden ===")
    delete_key = b'orden_nueva'
    table.delete(delete_key)
    print(f"Orden {delete_key.decode()} eliminada.")

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    connection.close()
    print("Conexión cerrada.")
