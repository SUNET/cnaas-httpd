FROM debian:buster

# Create directories
RUN mkdir -p /opt/cnaas
RUN mkdir /etc/cnaas-nms

# Setup script
COPY cnaas-setup.sh /opt/cnaas/cnaas-setup.sh
RUN /opt/cnaas/cnaas-setup.sh

# Prepare for supervisord, uwsgi, ngninx
COPY config/uwsgi.ini /opt/cnaas/venv/cnaas-nms/
COPY config/supervisord_app.conf /etc/supervisor/supervisord.conf
COPY config/nginx_app.conf /etc/nginx/sites-available/
COPY config/nginx.conf /etc/nginx/
COPY cert/* /etc/nginx/conf.d/

# Give nginx some special treatment
RUN unlink /etc/nginx/sites-enabled/default
RUN ln -s /etc/nginx/sites-available/nginx_app.conf /etc/nginx/sites-enabled/default
RUN chown www-data:www-data /var/log/nginx
RUN chown -R  www-data:www-data /var/log/nginx/
RUN chown -R www-data:www-data /var/lib/nginx
RUN mkdir -p /opt/cnaas/www/firmware
RUN chown www-data:www-data /var/lib/nginx/
RUN chown -R www-data:www-data /opt/cnaas

# Expose HTTPS
EXPOSE 1443

ENTRYPOINT supervisord -c /etc/supervisor/supervisord.conf
