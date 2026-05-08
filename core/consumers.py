import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, User, Order

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # We create a personal group for each user based on their ID
        self.room_group_name = f'chat_{self.user.id}'

        # Join personal room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        receiver_id = text_data_json.get('receiver_id')
        order_id = text_data_json.get('order_id')
        negotiated_price = text_data_json.get('negotiated_price')

        if not receiver_id or not message:
            return

        # Save message to DB
        msg = await self.save_message(self.user.id, receiver_id, message, order_id, negotiated_price)

        if not msg:
            return

        # Send message to receiver's group
        receiver_group_name = f'chat_{receiver_id}'
        
        message_data = {
            'type': 'chat_message',
            'id': msg.id,
            'message': message,
            'sender_id': self.user.id,
            'receiver_id': receiver_id,
            'sender_name': self.user.get_full_name() or self.user.username,
            'created_at': msg.created_at.isoformat(),
            'negotiated_price': str(negotiated_price) if negotiated_price else None
        }

        # Send to receiver
        await self.channel_layer.group_send(
            receiver_group_name,
            message_data
        )
        
        # Send back to sender to confirm and show in their UI
        await self.channel_layer.group_send(
            self.room_group_name,
            message_data
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content, order_id=None, negotiated_price=None):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
            order = None
            if order_id:
                order = Order.objects.get(id=order_id)
                if negotiated_price:
                    order.negotiated_price = negotiated_price
                    order.status = 'negotiating'
                    order.save()
            
            msg = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=content,
                order=order,
                negotiated_price=negotiated_price
            )
            
            # Simple Bot logic for admins
            if receiver.role == 'admin':
                bot_response = "Thank you for contacting AgriLink Support. Our team will get back to you shortly."
                if "verify" in content.lower():
                    bot_response = "To verify your account, ensure you have uploaded your documents in your profile. Our admins typically review these within 24-48 hours."
                elif "payment" in content.lower():
                    bot_response = "We support eSewa and Khalti. Payments are only available after farmer approval."
                
                Message.objects.create(
                    sender=receiver,
                    receiver=sender,
                    content=bot_response
                )
                # We should theoretically broadcast the bot message too, but simplified for now
                
            return msg
        except User.DoesNotExist:
            return None
