import pika
from dotenv import load_dotenv

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='synthesis')


channel.basic_publish(exchange='', routing_key='synthesis', body="{\"file_id\":\"645a89204195998764c2d466\"}")
print(" [x] Sent file id ")
connection.close()