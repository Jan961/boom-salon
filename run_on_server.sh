sudo pkill python
git checkout master
git pull
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations home
python manage.py migrate home
sudo setsid nohup python manage.py runserver 0.0.0.0:80 > nohup.log &
