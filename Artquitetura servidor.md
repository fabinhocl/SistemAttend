Arquitetura
O desenho mais adequado para seu ambiente de homologação é manter tudo em uma única VM, mas com os serviços isolados em containers, o que simplifica operação e ainda deixa a estrutura pronta para depois separar app e banco em produção.

Fluxo sugerido:

Internet → Nginx (HTTPS/443)

Nginx → Django/Gunicorn

Nginx → arquivos estáticos do Vue buildado

Django → PostgreSQL

Django/Celery → Redis

Gateway Pix/cartão → webhook HTTPS no Nginx → Django

Esse modelo funciona bem para homologação porque a VCN pública permite IP público para acesso externo, e a Oracle deixa claro que a instância em subnet pública pode receber public IPv4 para SSH e acesso pela internet.

Diagrama lógico

                Internet
                   |
             Reserved Public IP
                   |
                [ Nginx ]
          80/443   |   proxy
                   |
        -------------------------
        |           |           |
   [Vue build]  [Django]    [Webhook Pix/Cartão]
                    |
              ----------------
              |              |
         [PostgreSQL]     [Redis]


| Porta     | Uso                | Exposição                                                                                        |
| --------- | ------------------ | ------------------------------------------------------------------------------------------------ |
| 22        | SSH administrativo | Liberar só para seu IP fixo, porque a Oracle já trata porta 22 como regra comum de acesso Linux. |
| 80        | HTTP               | Pode abrir temporariamente para redirecionar para 443.                                           |
| 443       | HTTPS              | Aberta para testes, login, API e webhooks.                                                       |
| 5432      | PostgreSQL         | Não expor publicamente; deixar só interno no host/containers.                                    |
| 6379      | Redis              | Não expor publicamente; deixar só interno.                                                       |
| 8000      | Django interno     | Não expor publicamente; só Nginx conversa com ele.                                               |
| 5173/8080 | Vue dev            | Não usar em homologação pública; servir build estático pelo Nginx.                               |

Containers
Eu subiria estes containers:

nginx: proxy reverso, TLS, gzip, headers, servir o frontend.

app: Django + Gunicorn.

db: PostgreSQL com volume persistente.

redis: cache/broker.

worker: Celery, se o Attend já tiver tarefas assíncronas.

beat: Celery Beat, se houver rotinas agendadas.

Se quiser uma homologação mais enxuta, pode começar sem worker e beat, mas para sistema SaaS com cobrança e webhook eu prefiro já deixar Redis e worker previstos.

Docker Compose base
Abaixo está uma base de docker-compose.yml para você adaptar ao Attend:

version: "3.9"

services:
  nginx:
    image: nginx:stable-alpine
    container_name: attend_nginx
    depends_on:
      - app
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/conf.d:/etc/nginx/conf.d
      - ./infra/nginx/certs:/etc/nginx/certs
      - ./frontend/dist:/usr/share/nginx/html
      - static_data:/app/static
      - media_data:/app/media
    networks:
      - attend_net
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: attend_app
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - static_data:/app/static
      - media_data:/app/media
    expose:
      - "8000"
    networks:
      - attend_net
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    container_name: attend_db
    environment:
      POSTGRES_DB: attend
      POSTGRES_USER: attend_user
      POSTGRES_PASSWORD: troque_esta_senha
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - attend_net
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: attend_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - attend_net
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: attend_worker
    command: celery -A config worker -l info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - attend_net
    restart: unless-stopped

networks:
  attend_net:

volumes:
  postgres_data:
  redis_data:
  static_data:
  media_data: