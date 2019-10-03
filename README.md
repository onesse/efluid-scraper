# efluid-scraper
Scraper efluid

## Install Splash
In order to install Splash you should have Docker already installed. If you haven’t, install it  now with pip:

`sudo apt install docker.io`

Using docker you can install Splash:

`sudo docker pull scrapinghub/splash`

Now you can test if Splash is installed properly you have to start Splash server every time you want to use it:

`sudo docker run -p 8050:8050 scrapinghub/splash`
