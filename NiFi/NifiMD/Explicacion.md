#INSTRUCCIONES PARA LA SESIÓN:
##Si no existe previamente, crear la red compartida:
docker network create bigdata
Crea la red bigdata

##Despliegue de HBase
docker run -d --name hbase --hostname hbase --network bigdata -p 16000:16000 -p 16010:16010 -p 16020:16020 -p 16030:16030 -p 2181:2181 harisekhon/hbase:2.1
Levanta el contenedor con el parametro detach,llamado hbase  en la red bigdata, en los puertos 16000:16000, 16010:16010, 16020:16020, 16030:16030 ,2181:2181 y luego indica la imagen 

##Despliegue de Neo4j
docker run -d --name neo4j --network bigdata -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -e NEO4J_PLUGINS='["apoc"]' -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true neo4j:5
Levanta el contenedor con el parametro detach,llamado neo4j  en la red bigdata, en los puertos 7474:7474,7687:7687 usa usuario/contraseña como auth y añade el plugin apoc, al apoc le habilita la exportación y la importación y luego indica la imagen


##Despliegue de Apache NiFi
docker run -d --name nifi --network bigdata -p 8443:8443 -e NIFI_WEB_HTTPS_PORT=8443 -e NIFI_WEB_PROXY_HOST=localhost:8443 -e HADOOP_CONF_DIR=/opt/nifi/hadoop-conf -v $(pwd)/nifi/hadoop-conf:/opt/nifi/hadoop-conf:ro apache/nifi:2.6.0
Levanta el contenedor con el parametro detach,llamado nifi, en la red bigdata, en los puertos 8443:8443, el puerto de HTTPS de nifi tambien es el 8443 y el de proxy tambien, luego le indica donde esta la carpeta de configuracion de hadoop y el volumen como solo lectura y como ultimo indica la imagen que se va a levantar


##Ver usuario y contraseña autogenerado en NiFi:
NiFi genera automáticamente un usuario y contraseña en el primer arranque. Para consultarlos:
docker logs -f nifi | egrep -i "generated|credentials|single-user|username|password"
De los logs de nifi, busca los que concidan con generated o credentials o single-user o username o password


##Instalar procesador para neo4j:
NiFi no incorpora por defecto todos los componentes necesarios para trabajar con Neo4j. Será necesario instalar los siguientes NAR (NiFi Archive).
docker exec -it -u root nifi bash -c '
  cd /opt/nifi/nifi-current/lib && \
  curl -fsSLO https://repo1.maven.org/maven2/org/apache/nifi/nifi-graph-nar/2.6.0/nifi-graph-nar-2.6.0.nar && \
  curl -fsSLO https://repo1.maven.org/maven2/org/apache/nifi/nifi-neo4j-cypher-service-nar/2.6.0/nifi-neo4j-cypher-service-nar-2.6.0.nar && \
  curl -fsSLO https://repo1.maven.org/maven2/org/apache/nifi/nifi-graph-client-service-api-nar/2.6.0/nifi-graph-client-service-api-nar-2.6.0.nar && \
  chown nifi:nifi nifi-graph-*.nar nifi-neo4j-*.nar
'
En la bash del contenedor nifi, siendo root ejecuta el cambio de carpeta, posteriormente descarga las librerías/paquetes y le cambia el propietario a los archivos ya que se uso root antes

docker restart nifi
Reinicia el docker nifi

##Configurar el conector HDFS:  
docker cp hive2:/opt/hadoop/etc/hadoop/core-site.xml ./nifi/hadoop-conf/core-site.xml
docker cp hive2:/opt/hadoop/etc/hadoop/hdfs-site.xml ./nifi/hadoop-conf/hdfs-site.xml
Copia el archivo desde el directorio del docker hive2: al la carpeta ./nifi

#Crear directorio de trabajo para NiFi en HDFS

docker exec -it hive2 bash -lc "
  hdfs dfs -mkdir -p /user/nifi && \
  hdfs dfs -chown -R nifi /user/nifi
"
En la bash de hive2 crea la carpeta, y campia el propietaro

Antes de continuar, comprobar que:
   - El NameNode no se encuentra en Safe Mode.
   - Todos los DataNodes aparecen en estado saludable(health=OK).
   - El acceso a HDFS funciona correctamente desde el contenedor de Hadoop.

##Instalar el conector HBASE: 

Descargar los componentes NAR exactos para la versión 2.6.0 (tanto las librerías base de Hadoop como el cliente y procesadores de HBase 2) dentro de /opt/nifi/nifi-current/lib:

docker exec -it -u root nifi bash -c '
  cd /opt/nifi/nifi-current/lib && \
  VER=2.6.0 && \
  BASE=https://repo1.maven.org/maven2/org/apache/nifi && \
  curl -fsSLO $BASE/nifi-hadoop-libraries-nar/$VER/nifi-hadoop-libraries-nar-$VER.nar && \
  curl -fsSLO $BASE/nifi-hadoop-nar/$VER/nifi-hadoop-nar-$VER.nar && \
  curl -fsSLO $BASE/nifi-hbase_2-client-service-nar/$VER/nifi-hbase_2-client-service-nar-$VER.nar && \
  curl -fsSLO $BASE/nifi-hbase-nar/$VER/nifi-hbase-nar-$VER.nar && \
  chown nifi:nifi nifi-hadoop-*.nar nifi-hbase*.nar
'
En la bash del contenedor nifi, siendo root ejecuta el cambio de carpeta, posteriormente descarga las librerías/paquetes y le cambia el propietario a los archivos ya que se uso root antes

Una vez copiados los archivos al directorio de librerías de NiFi, reiniciar nuevamente el contenedor para que los nuevos procesadores estén disponibles.

docker restart nifi

Resumen

Apache NiFi 2.6.0---> https://localhost:8443/nifi ---> 8443 (HTTPS) ---> Autogenerado (ver logs) ---> Autogenerada (ver logs)
Neo4j 5 ---> http://localhost:7474 / bolt://neo4j:7687 ,7474 (HTTP), 7687 (Bolt) ---> neo4j ---> password
HBase 2.1 ---> http://localhost:16010 (Master UI) ---> 16000, 16010, 16020, 16030, 2181 (ZK) ---> Sin autenticación --->Sin autenticación
HDFS (hive2) ---> hdfs://hive2:9000 (interno en red bigdata) ---> 9000 (RPC) ---> nifi (propietario /user/nifi) ---> Sin autenticación

Obtener credenciales de NiFi (primer arranque)
NiFi 2.6.0 tarda unos 40–60 segundos en levantar Jetty y generar el usuario único. Ejecuta:
docker logs -f nifi | egrep -i "generated|credentials|single-user|username|password"
De los logs de nifi, busca los que concidan con generated o credentials o single-user o username o password
