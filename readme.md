#Задание 2. Настройка защищённого соединения и управление доступом

##Структура проекта:

kafka-ssl-cluster/
├── docker-compose.yml
├── ca.cnf
├── ca.crt
├── ca.key
├── ca.pem
├── kafka-1-creds/
│   ├── kafka-1.cnf
│   ├── kafka-1.crt
│   ├── kafka-1.csr
│   ├── kafka-1.key
│   ├── kafka-1.p12
│   ├── kafka.kafka-1.keystore.pkcs12
│   ├── kafka.kafka-1.truststore.jks
│   ├── kafka-1_sslkey_creds
│   ├── kafka-1_keystore_creds
│   └── kafka-1_truststore_creds
├── kafka-2-creds/
│   ├── ... (аналогично kafka-1-creds)
├── kafka-3-creds/
│   ├── ... (аналогично kafka-1-creds)
├── client-ssl.properties
├── producer.py
└── consumer.py


##1. Создание сертификатов для каждого брокера

Сначала создадим сертификаты для всех трех брокеров (kafka-1, kafka-2, kafka-3):

###Создание корневого сертификата (Root CA)

*Создаем файл конфигурации ca.cnf*
cat > ca.cnf << 'EOF'
[ policy_match ]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[ req ]
prompt = no
distinguished_name = dn
default_md = sha256
default_bits = 4096
x509_extensions = v3_ca

[ dn ]
countryName = RU
organizationName = Yandex
organizationalUnitName = Practice
localityName = Moscow
commonName = yandex-practice-kafka-ca

[ v3_ca ]
subjectKeyIdentifier=hash
basicConstraints = critical,CA:true
authorityKeyIdentifier = keyid:always,issuer:always
keyUsage = critical,keyCertSign,cRLSign
EOF

*Генерируем корневой сертификат*
openssl req -new -nodes -x509 -days 365 -newkey rsa:2048 -keyout ca.key -out ca.crt -config ca.cnf

*Объединяем сертификат и ключ в один файл*
cat ca.crt ca.key > ca.pem

##2. Создание сертификатов для брокеров

###Создаем директории для каждого брокера: 

mkdir -p kafka-{1,2,3}-creds

Для каждого брокера (kafka-1, kafka-2, kafka-3) необходимо выполнить следующие действия:
###Подготовка структуры каталогов: 

mkdir -p kafka-{1,2,3}-creds

###Создание конфигурационного файла для каждого брокера:

*Пример для kafka-1 (аналогично для kafka-2 и kafka-3):*
cat > kafka-1-creds/kafka-1.cnf << 'EOF'
[req]
prompt = no
distinguished_name = dn
default_md = sha256
default_bits = 4096
req_extensions = v3_req

[dn]
countryName = RU
organizationName = Yandex
organizationalUnitName = Practice
localityName = Moscow
commonName = kafka-1

[v3_ca]
subjectKeyIdentifier = hash
basicConstraints = critical,CA:true
authorityKeyIdentifier = keyid:always,issuer:always
keyUsage = critical,keyCertSign,cRLSign

[v3_req]
subjectKeyIdentifier = hash
basicConstraints = CA:FALSE
nsComment = "OpenSSL Generated Certificate"
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = kafka-1
DNS.2 = kafka-1.example.com
DNS.3 = localhost
IP.1 = 127.0.0.1
EOF

###Генерация приватного ключа и CSR (Certificate Signing Request):

openssl req -new \
    -newkey rsa:2048 \
    -keyout kafka-1-creds/kafka-1.key \
    -out kafka-1-creds/kafka-1.csr \
    -config kafka-1-creds/kafka-1.cnf \
    -nodes

###Подпись CSR корневым сертификатом:

openssl x509 -req \
    -days 3650 \
    -in kafka-1-creds/kafka-1.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out kafka-1-creds/kafka-1.crt \
    -extfile kafka-1-creds/kafka-1.cnf \
    -extensions v3_req

###Создание PKCS12 хранилища:

openssl pkcs12 -export \
    -in kafka-1-creds/kafka-1.crt \
    -inkey kafka-1-creds/kafka-1.key \
    -chain \
    -CAfile ca.pem \
    -name kafka-1 \
    -out kafka-1-creds/kafka-1.p12 \
    -password pass:your-password

###Создание keystore для Kafka

keytool -importkeystore \
    -deststorepass your-password \
    -destkeystore kafka-1-creds/kafka.kafka-1.keystore.pkcs12 \
    -srckeystore kafka-1-creds/kafka-1.p12 \
    -deststoretype PKCS12 \
    -srcstoretype PKCS12 \
    -noprompt \
    -srcstorepass your-password

###Создание truststore для Kafka:

keytool -import \
    -file ca.crt \
    -alias ca \
    -keystore kafka-1-creds/kafka.kafka-1.truststore.jks \
    -storepass your-password \
    -noprompt


###Сохранение паролей:

echo "your-password" > kafka-1-creds/kafka-1_sslkey_creds
echo "your-password" > kafka-1-creds/kafka-1_keystore_creds
echo "your-password" > kafka-1-creds/kafka-1_truststore_creds

##3. Запускаем Docker Compose для кластера Kafka с SSL
docker-compose up -d

##4. Настройка ACL (Access Control Lists)

После запуска кластера настроим права доступа к топикам:

docker run -it --rm --network project_5_2_default -v $(pwd):/secrets confluentinc/cp-kafka:7.0.1 bash

*Внутри контейнера:*

*Настраиваем переменные окружения*
export KAFKA_OPTS="-Djava.security.auth.login.config=/secrets/kafka_client_jaas.conf"
export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"

*Создаем файл конфигурации JAAS для клиента*
cat > /secrets/kafka_client_jaas.conf << EOF
KafkaClient {
    org.apache.kafka.common.security.plain.PlainLoginModule required
    username="admin"
    password="admin-secret";
};
EOF

*Создаем топики*
kafka-topics --bootstrap-server kafka-1:9093 --command-config /secrets/client-ssl.properties --create --topic topic-1 --partitions 3 --replication-factor 3
kafka-topics --bootstrap-server kafka-1:9093 --command-config /secrets/client-ssl.properties --create --topic topic-2 --partitions 3 --replication-factor 3

*Настраиваем ACL для topic-1 (разрешаем все операции)*
kafka-acls --bootstrap-server kafka-1:9093 --command-config /secrets/client-ssl.properties --add --allow-principal User:admin --operation All --topic topic-1 --group '*'

*Настраиваем ACL для topic-2 (разрешаем только запись)*
kafka-acls --bootstrap-server kafka-1:9093 --command-config /secrets/client-ssl.properties --add --allow-principal User:admin --producer --topic topic-2
kafka-acls --bootstrap-server kafka-1:9093 --command-config /secrets/client-ssl.properties --add --deny-principal User:admin --consumer --topic topic-2 --group '*'

##5. Python скрипты для тестирования

###Создадим файл client-ssl.properties для клиентов:

security.protocol=SSL
ssl.truststore.location=ca.pem
ssl.keystore.location=client.keystore.p12
ssl.keystore.password=your-password
ssl.key.password=your-password


##6. Запуск и тестирование

- Запустите кластер: docker-compose up -d

- Настройте ACL (как показано выше)

- Запустите producer: python3 producer.py

- Запустите consumer: python3 consumer.py

##Ожидаемый результат:

- Consumer успешно читает сообщения из topic-1

- При попытке чтения из topic-2 получает ошибку доступа

