const raw = {
  matricula: '1',
  nombre: 'GADANO JUAN CARLOS',
  ramo: 'Patrimoniales y Vida',
  provincia: 'CABA',
  localidad: null,
  telefono: '',
  email: 'jcgagadno@rojasygadano.com.ar',
  estado_contacto: 'Sin contactar',
  companias: null,
  documento: 'Libreta Enrolamiento 8253149',
  cuit: '20082531492'
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
    ...raw,
    // Campos de identidad
    matricula:         getVal("matricula", "productor_matricula", "nro_matricula"),
    nombre:            getVal("nombre", "productor_apellido_nombre", "nombre_completo"),
    documento:         getVal("documento", "productor_id"),
    cuit:              getVal("cuit", "productor_id", "id"),
    tipo_id:           getVal("tipo_id", "productor_tipo_id"),
    ramo:              getVal("ramo"),
    // Campos de ubicación
    provincia:         getVal("provincia"),
    localidad:         getVal("localidad", "ciudad"),
    domicilio:         getVal("domicilio"),
    cod_postal:        getVal("cod_postal", "cp"),
    // Contacto
    telefono:          getVal("telefono", "telefonos"),
    email:             getVal("email", "correo", "correos"),
    // Datos regulatorios
    resolucion:        getVal("resolucion"),
    fecha_resolucion:  getVal("fecha_resolucion"),
    // CRM
    estado_contacto:   getVal("estado_contacto") || "Sin Contactar",
    observaciones:     getVal("observaciones") || "",
    companias:         getVal("companias", "sociedades") || "",
  };
}

const parsed = normalizePAS(raw);
console.log("matricula:", parsed.matricula);
console.log("nombre:", parsed.nombre);
console.log("provincia:", parsed.provincia);
console.log("localidad:", parsed.localidad);
