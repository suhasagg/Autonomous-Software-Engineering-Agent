FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package
FROM eclipse-temurin:21-jre
RUN apt-get update && apt-get install -y --no-install-recommends git maven && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/*.jar /app.jar
ENTRYPOINT ["java","-jar","/app.jar"]
