// Foto della vetrina: pezzi realizzati e decorati durante un'esperienza in laboratorio.
// I file stanno in public/foto (ridimensionati e senza dati EXIF/posizione).
// Ogni servizio e il pacchetto hanno la loro foto, cercata per slug.

export const fotoBenvenuto = {
  src: "/foto/benvenuto-tre-pezzi.jpg",
  alt: "Una ciotola e due tazzine in ceramica dipinte a mano su un tavolo",
};

export const fotoChiSiamo = {
  src: "/foto/chi-siamo-tazzine.jpg",
  alt: "Due tazzine in ceramica: una a fasce verde, gialla e viola, l'altra marrone con l'interno verde",
};

const fotoPerSlug = {
  "corso-tornio-base": "Ciotola tornita con l'interno giallo e il decoro geometrico verde e giallo",
  "corso-decorazione": "Tazzina dipinta a fasce verde, gialla e viola con puntini neri",
  "corso-cottura-smaltatura": "Interno di una ciotola smaltata in giallo, visto dall'alto",
  "esperienza-tornio": "Ciotola capovolta: il decoro geometrico verde e giallo visto da vicino",
  "esperienza-decorazione": "Tazzina marrone con l'interno verde, decorata con segni e puntini neri",
  "giornata-in-bottega": "Una ciotola e due tazzine viste dall'alto",
  coworking: "Interno verde di una tazzina, visto dall'alto",
};

// Restituisce { src, alt } oppure null se per quello slug non c'è una foto
export function fotoDi(slug) {
  const alt = fotoPerSlug[slug];
  return alt ? { src: `/foto/${slug}.jpg`, alt } : null;
}
