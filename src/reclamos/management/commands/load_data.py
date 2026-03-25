from django.core.management.base import BaseCommand
import json
from reclamos.models import Reclamo, Contribuyente  # Asegúrate de que tus modelos estén bien importados

class Command(BaseCommand):
    help = 'Carga datos desde un archivo JSON'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
            
            # Aquí va el procesamiento y la carga de los datos...
            for item in data:
                # Suponiendo que el JSON tiene una estructura compatible con tus modelos.
                # Asegúrate de adaptar esto según la estructura de tus modelos.
                
                contribuyente_data = item.get('contribuyente', {})
                contribuyente, created = Contribuyente.objects.get_or_create(
                    dni=contribuyente_data.get('dni'),
                    defaults={'apellido': contribuyente_data.get('apellido', ''),
                              'nombres': contribuyente_data.get('nombres', '')}
                )

                # Puedes adaptar lo siguiente a la estructura de tu JSON y modelo
                Reclamo.objects.create(
                    usuario_id=item['usuario_id'],
                    id_contribuyente=contribuyente,
                    tipo_reclamo_id=item['tipo_reclamo_id'],
                    prioridad=item['prioridad'],
                    titulo=item['titulo'],
                    descripcion=item['descripcion'],
                    estado_id=item['estado_id']
                )

            self.stdout.write(self.style.SUCCESS('Datos cargados correctamente desde el archivo JSON'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al cargar los datos: {e}'))
