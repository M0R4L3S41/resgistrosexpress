from datetime import date
from cep import Transferencia

# Validar la transferencia
tr = Transferencia.validar(
    fecha=date(2024, 10, 13),
    clave_rastreo='241014075546348566I',
    emisor='40127',  # STP
    receptor='90722',  # BBVA
    cuenta='722969010354464015',
    monto=1,
)

# Verificar si la transferencia fue encontrada
if tr is None:
    print("Transferencia no encontrada.")
else:
    # Descargar el PDF
    pdf_content = tr.descargar()

    # Guardar el archivo PDF en una ubicación específica
    with open("transferencia.pdf", "wb") as f:
        f.write(pdf_content)
        print("PDF guardado como 'transferencia.pdf'")
