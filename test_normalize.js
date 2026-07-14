const raw = {
  matricula: "100000",
  nombre: "MARIA LAURA LEGUIZAMON",
  provincia: "Buenos Aires",
  localidad: "CABA"
};

function normalizePAS(raw) {
  if (!raw) return raw;
  
  // Buscar las keys de forma case-insensitive
  const getVal = (...keys) => {
    for (const key of keys) {
      for (const rawKey in raw) {
        if (rawKey.toLowerCase() === key.toLowerCase() && raw[rawKey] !== null && raw[rawKey] !== undefined && raw[rawKey] !== "") {
          return raw[rawKey];
        }
      }
    }
    return null;
  };

  return {
    matricula:         getVal("matricula", "productor_matricula", "nro_matricula"),
    nombre:            getVal("nombre", "productor_apellido_nombre", "nombre_completo"),
    provincia:         getVal("provincia"),
    localidad:         getVal("localidad", "ciudad"),
    ...raw,
  };
}

console.log(normalizePAS(raw));
