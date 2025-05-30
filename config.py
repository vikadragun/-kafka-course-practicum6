config = {
    'bootstrap.servers': 'kafka-1:9093,kafka-2:9094,kafka-3:9095',
    'security.protocol': 'ssl',
    'ssl.ca.location': 'ca.crt',
    'ssl.certificate.location': 'kafka-1-creds/kafka-1.crt',
    'ssl.key.location': 'kafka-1-creds/kafka-1.key',
    'topic1': 'topic-1',
    'topic2': 'topic-2',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest'
}