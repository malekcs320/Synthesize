import pika
from dotenv import load_dotenv

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='synthesis')


channel.basic_publish(exchange='', routing_key='syntheses', body="{\"file_id\":\"645b7bd1948e0d0d573a68bb\"}")
print(" [x] Sent file id ")
connection.close()