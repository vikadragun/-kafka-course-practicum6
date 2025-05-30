from confluent_kafka import Producer
from config import config
import sys

def delivery_report(err, msg):
    """Callback-функция для обработки результатов доставки"""
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Создаем продюсера с SSL-конфигурацией
producer_conf = {
    'bootstrap.servers': config['bootstrap.servers'],
    'security.protocol': config['security.protocol'],
    'ssl.ca.location': config['ssl.ca.location'],
    'ssl.certificate.location': config['ssl.certificate.location'],
    'ssl.key.location': config['ssl.key.location']
}

producer = Producer(producer_conf)

# Отправка сообщений в topic-1 (полный доступ)
for i in range(5):
    producer.produce(
        config['topic1'],
        f'Message {i} to topic-1',
        callback=delivery_report
    )
    print(f"Sending message {i} to {config['topic1']}")

# Отправка сообщений в topic-2 (только запись)
for i in range(5):
    try:
        producer.produce(
            config['topic2'],
            f'Message {i} to topic-2',
            callback=delivery_report
        )
        print(f"Sending message {i} to {config['topic2']}")
    except Exception as e:
        print(f"Error sending to {config['topic2']}: {str(e)}")


producer.flush()