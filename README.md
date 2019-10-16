# efluid-scraper
Scraper e-fluid

#### Etape 1
Mettre en place un environnement virtuel

#### Etape 2
`pip install -r requirements.txt`

#### Etape 3
créer un dossier credentials/ et y ajouter le fichier ELD.json contenant logins et mots de passe.

#### Etape 4
Lancer le spider :

`scrapy crawl login -a filename=./test-efluid-scraper.xlsx -o output.csv`

#### Etape 5
Lancer le spider via votre script:

https://docs.scrapy.org/en/latest/topics/practices.html 