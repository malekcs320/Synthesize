import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='synthesize')

channel.basic_publish(exchange='', routing_key='synthesize', body="{\"transcript_id\":\"64541f5872e4b3f6763ac874\",\"notes_id\" : \"645534ccd258c8a896b63c9f\"}")
print(" [x] Sent 'Hello World!'")
connection.close()