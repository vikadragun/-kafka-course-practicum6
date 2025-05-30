from confluent_kafka import Consumer, KafkaException
from config import config
import sys

# Создаем консьюмера с SSL-конфигурацией
consumer_conf = {
    'bootstrap.servers': config['bootstrap.servers'],
    'security.protocol': config['security.protocol'],
    'ssl.ca.location': config['ssl.ca.location'],
    'ssl.certificate.location': config['ssl.certificate.location'],
    'ssl.key.location': config['ssl.key.location'],
    'group.id': config['group.id'],
    'auto.offset.reset': config['auto.offset.reset']
}

consumer = Consumer(consumer_conf)


def consume_messages(topic):
    print(f"Consuming from {topic}:")
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            print(f"Received from {msg.topic()}: {msg.value().decode('utf-8')}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


# Чтение из topic-1 (разрешено)
consume_messages(config['topic1'])

# Попытка чтения из topic-2 (должна завершиться ошибкой)
print(f"\nAttempting to consume from {config['topic2']}:")
try:
    consume_messages(config['topic2'])
except Exception as e:
    print(f"Error consuming from {config['topic2']}: {str(e)}")