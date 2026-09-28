# Market Motion Studio

Cette application transforme des indicateurs du marché des actions A en vidéos verticales pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4. Rien d'autre n'est à installer.

## Choisir un marché

Les paramètres déterminent de quel marché l'application tire ses cotations ; les actions A par défaut. Le changement prend effet après le redémarrage de l'application.

- **Actions A** : les sept pages sont disponibles.
- **Hong Kong** : la matrice des rendements et le calendrier fonctionnent ; la course de secteurs utilise les quatre sous-indices Hang Seng ; **il n'existe pas de chiffre pour l'ensemble du marché, cette page est donc masquée**.
- **États-Unis** : la matrice des rendements et le calendrier fonctionnent ; la course de secteurs utilise dix ETF sectoriels SPDR ; la page des volumes ne garde que le mode quotidien, car le point d'accès minute ne sert pas de données américaines ; **les montants sont en dollars et la page du volume d'échanges du marché est masquée**.

## Volume d'échanges du marché

Le montant échangé chaque jour sur tout le marché : les montants des indices composites de Shanghai et de Shenzhen additionnés, une barre par séance.

- Seules les journées où tous les marchés retenus ont traité sont conservées, afin qu'un jour férié sur un seul marché ne fasse pas paraître le total en chute libre.
- Une séance encore en cours est écartée. Une journée inachevée ne contient que sa fixation d'ouverture et se dessinerait comme une barre collée à l'axe.
- Ou regarder un seul segment : chaque bourse, chaque marché principal, STAR, ChiNext. Les marchés principaux sont déduits du total de la bourse moins son marché de croissance ; le BSE 50 reste une mesure de composantes.
- Seul le marché des actions A donne un total pour l'ensemble du marché. Avec Hong Kong ou les États-Unis, la page est retirée de la navigation.

## Volume et rotation

Le volume d'un titre face à son taux de rotation, en deux panneaux superposés.

- D'une séance à l'autre, volume et taux de rotation sont proportionnels : les deux panneaux ont donc presque la même forme. À l'intérieur d'une journée, le volume par minute et la rotation cumulée n'ont plus rien de commun, et c'est l'image la plus intéressante.
- La source intrajournalière ne conserve que les dernières séances ; ce mode propose donc celles-là plutôt qu'une date quelconque.
- Les données minute ne sont servies que pour les actions A et Hong Kong ; aux États-Unis ce mode n'est pas proposé.

## Course de secteurs

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/sector-race.png)

Un ensemble de secteurs ou d'actions, dessiné en barres horizontales qui se dépassent, l'ordre changeant jusqu'à la dernière image.

- Deux mesures : la variation de la période en % et son volume en centaines de millions de yuans. Changer de mesure ne fait que re-teinter les mêmes données ; cela ne relance pas la requête.
- Quatre listes : secteurs Shenwan de niveau 1, thèmes en vue, personnalisée (à cocher) et actions individuelles (ajout par recherche). La liste personnalisée démarre remplie avec les secteurs Shenwan de niveau 1.
- Les listes intégrées suivent le marché : secteurs Shenwan de niveau 1 et thèmes en vue pour les actions A, quatre sous-indices Hang Seng pour Hong Kong, dix ETF sectoriels SPDR pour les États-Unis. Les listes personnalisée et actions existent sur tous les marchés.
- La période peut être de 1, 3, 6 ou 12 mois, ou des dates de début et de fin personnalisées.
- Une liste a un nombre minimum et maximum d'entrées — trop peu, ce n'est pas une course ; trop, c'est un fouillis.

## Matrice des rendements

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/monthly-matrix.png)

Des barres mensuelles disposées en grille : le mode année montre la saisonnalité d'un instrument sur dix ans, le mode comparaison met plusieurs instruments côte à côte pour montrer la rotation.

- Mode année : choisissez un instrument (recherche ou un indice large prédefini) ; la plage va de 1 à 10 ans ou tous. Une requête renvoie dix ans de barres mensuelles.
- Mode comparaison : 2 à 14 instruments d'une liste (secteurs de niveau 1 / thèmes / indices larges / personnalisée / actions) côte à côte, sur 6 à 48 mois.
- La grille s'allume case par case dans l'ordre du temps ; la fin présente le meilleur et le pire mois de la plage, entre autres statistiques.
- Les données mensuelles couvrent une décennie d'un coup, il n'y a donc pas de limite quotidienne ici — mais trop d'instruments débordent du cadre.

## Calendrier des hausses et baisses

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/gain-calendar.png)

Toute action ou tout indice chinois, sa hausse ou baisse quotidienne disposée en cellules de calendrier par mois : rouge à la hausse, vert à la baisse.

- Recherche par code, nom ou pinyin ; les préréglages sont des indices larges. Seuls les instruments du marché sélectionné.
- La liste de favoris est partagée avec la page d'actions de l'application — un favori ajouté des deux côtés apparaît des deux côtés.
- La période est de 1, 3, 6 ou 12 mois, ou personnalisée ; un instrument seul reste soumis à la limite d'environ 640 jours calendaires.
- Les statistiques finales donnent le nombre de séances en hausse et en baisse.

## Plan DCA

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/dca-plan.png)

Acheter un titre à montant et cadence fixes — chaque jour de bourse, chaque semaine ou chaque mois — et voir en animation ce que la discipline a produit.

- Les instruments en un clic suivent le marché : ETF larges et or sur les actions A, fonds indiciels de Hong Kong, SPY, QQQ et GLD aux États-Unis.
- Le montant et la fréquence se règlent librement ; la période fait trois, cinq ou dix ans, ou remonte aussi loin que les données le permettent (environ treize ans).
- Le rendement est calculé sur des clôtures rétro-ajustées, sans frais. Le résultat décrit la série de prix, pas une facture que qui que ce soit aurait pu exécuter.

## Rendement de position

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/position.png)

Un seul achat, conservé des années — un million dans 中国平安 en 2015, par exemple — animé comme ce que la valeur et le rendement ont fait.

- Les noms proposés suivent le marché : en Chine, les actions que l'on dit réellement avoir gardées (Ping An, Moutai, CMB…), à Hong Kong Tencent, HSBC et le Tracker Fund, aux États-Unis Apple, Berkshire et SPY.
- Le capital initial et la période de détention sont à vous ; la période couvre trois, cinq ou dix ans, ou aussi loin que les données remontent (environ treize ans).
- Le rendement est calculé sur des cours rétro-ajustés — dividendes réinvestis, sans frais. L'ajustement rétroactif s'ancre à l'introduction en bourse et cumule les dividendes vers l'avant, si bien que les premières années d'un gros versant ne deviennent jamais négatives, ce que l'ajustement avant peut produire.

## Vidéo

L'image est toujours en 9:16. Tout le reste vous appartient.

- La durée change le rythme, elle ne raccourcit pas l'animation : l'ouverture, la croissance des barres et les statistiques finales sont réparties sur la longueur choisie.
- Les marges sont notées par rapport à une image de 1080×1920 puis mises à l'échelle de la résolution d'export ; une mise en page réglée une fois tient à toutes les tailles. La marge gauche détermine aussi où se posent les graduations : trop petite, les chiffres sortent de l'image.
- Les repères de zone sûre délimitent ce qu'une application mobile recouvre de sa propre interface. Ils sont tracés dans l'aperçu et jamais dans un fichier.

## Où vont les vidéos

Les exports sont écrits dans un dossier que vous choisissez par un sélecteur. Tant qu'aucun n'est choisi, le premier export le demande puis le retient ; les paramètres permettent de le changer ou de l'oublier.

## Image d'arrière-plan

La page des paramètres peut placer une image derrière la fenêtre, assombrie. Les cartes et les panneaux restent opaques et le volet de navigation ne laisse passer qu'un peu de l'image, qui apparaît surtout autour d'eux. L'aperçu vidéo possède son propre fond opaque et n'est pas concerné.

- Choisissez une image sur l'ordinateur ou utilisez directement l'un des fonds d'écran et images d'écran de verrouillage fournis avec Windows.
- L'image choisie est copiée dans le dossier propre à l'application : déplacer ou supprimer l'original ne touche pas l'arrière-plan.
- Le curseur d'intensité du voile détermine à quel point l'image est atténuée, de 30 % à 95 %.
- Aucune image n'est affichée tant que le contraste élevé est activé.
## Fond de l'animation

La page Paramètres permet de changer ce sur quoi l'animation est dessinée : le dégradé intégré, deux couleurs de votre choix, ou une image. Cela vaut pour l'aperçu, pour la vidéo exportée et pour l'image de couverture : les trois sont dessinés par le même moteur, il n'y a donc pas de « joli dans l'aperçu, différent dans le fichier ».

- Pour les couleurs, vous donnez un ton du haut et un ton du bas, et l'image passe de l'un à l'autre. Les tons sombres conviennent : chaque teinte de texte est claire et un fond clair rend les chiffres difficiles à lire.

- Choisir une image fonctionne comme pour le fond de la fenêtre : une image de votre ordinateur, ou un fond d'écran fourni par Windows. Celle que vous choisissez est copiée dans le dossier de l'application.

- L'image remplit le cadre et le surplus est rogné : ses proportions ne sont jamais étirées.

- Le curseur d'assombrissement règle à quel point l'image est ramenée vers le fond propre à la page, de 20 % à 95 %.

## Les données, et ce qu'elles ne diront pas

Les cours viennent des points d'accès publics de Tencent Finance, et l'image cite toujours la source. Ces vidéos décrivent ce qui s'est déjà échangé. Elles sont fournies à titre indicatif et ne constituent pas un conseil en investissement.

- Les montants sont convertis en centaines de millions de yuans, et le volume passe à une unité plus grande dès que les chiffres l'exigent, pour que l'axe reste lisible.
- Les montants sont convertis en centaines de millions — de yuans sur le continent et à Hong Kong, de dollars aux États-Unis. Chaque marché garde sa propre devise.
- Une période de plus de 640 jours civils environ est refusée plutôt que tronquée en silence, car c'est tout ce qu'une requête à la source renvoie.

## Mise à jour

Quand le Microsoft Store propose une version plus récente, un bouton **Mettre à jour** apparaît à côté de Paramètres dans le volet de navigation ; un clic l'installe.

- Il n'apparaît que si le Store a réellement une version plus récente. Une version de développement ou installée à côté ne le voit jamais, et c'est normal.
- L'application se ferme pendant l'installation et redémarre sur la nouvelle version, et le bouton disparaît. Si un export est en cours, elle demande d'abord.
- Si l'installation échoue, la raison est donnée — Wi-Fi uniquement, batterie trop faible — et la mise à jour peut aussi être installée depuis le Microsoft Store.

## Un problème ?

Écrivez à gaqo@outlook.com en disant ce que vous faisiez et ce que vous attendiez à la place. Le numéro de version figure sur la page des paramètres.
