import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LocationConsumer(AsyncWebsocketConsumer):
    """
    CONSUMER DE GEOLOCALIZACIÓN (DANGO CHANNELS):
    Gestiona la comunicación bidireccional para el rastreo en tiempo real.
    - Los clientes se suscriben al grupo 'location_<vendor_id>'.
    - Los vendedores envían sus coordenadas, que se retransmiten a todos los suscriptores.
    """
    async def connect(self):
        self.vendor_id = self.scope['url_route']['kwargs']['vendor_id']
        self.group_name = f"location_{self.vendor_id}"

        # Unirse al grupo específico del vendedor
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Abandonar el grupo al desconectarse
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        RECIBIR COORDENADAS (SECURITY-FIRST):
        Procesa el mensaje y solo permite la difusión si el emisor es el VENDEDOR dueño del ID.
        """
        user = self.scope.get('user')
        
        # VALIDACIÓN DE IDENTIDAD: Solo el dueño del vendor_id puede emitir
        if not user or not user.is_authenticated or str(user.id) != self.vendor_id:
            # SRE: Intento de suplantación detectado o usuario no autorizado
            return

        try:
            data = json.loads(text_data)
            lat = data.get('lat')
            lng = data.get('lng')

            if lat is not None and lng is not None:
                # Transmitir la ubicación a todos los usuarios en el grupo
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'location_update',
                        'lat': lat,
                        'lng': lng,
                        'vendor_id': self.vendor_id
                    }
                )
        except json.JSONDecodeError:
            pass

    async def location_update(self, event):
        """
        ENVIAR AL CLIENTE:
        Método encargado de enviar los datos del grupo hacia el WebSocket del navegador.
        """
        await self.send(text_data=json.dumps({
            'lat': event['lat'],
            'lng': event['lng'],
            'vendor_id': event['vendor_id']
        }))
