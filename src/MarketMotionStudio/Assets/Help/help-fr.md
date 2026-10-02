# Market Motion Studio

Cette application transforme des indicateurs du marché des actions A en vidéos verticales pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4. Rien d'autre n'est à installer.

## Choisir un marché

Les paramètres déterminent de quel marché l'application tire ses cotations ; les actions A par défaut. Le changement prend effet après le redémarrage de l'application.

- **Actions A** : les huit pages sont disponibles.
- **Hong Kong** : la matrice des rendements et le calendrier fonctionnent ; la course de secteurs utilise les quatre sous-indices Hang Seng ; **il n'existe pas de chiffre pour l'ensemble du marché, cette page est donc masquée**.
- **États-Unis** : la matrice des rendements et le calendrier fonctionnent ; la course de secteurs utilise dix ETF sectoriels SPDR ; la page des volumes ne garde que le mode quotidien, car le point d'accès minute ne sert pas de données américaines ; **les montants sont en dollars et la page du volume d'échanges du marché est masquée**.



## Passer d'une page à l'autre

Les deux boutons à gauche de la barre de titre reculent et avancent parmi les pages visitées, comme le fait un navigateur : **Alt+Gauche** et **Alt+Droite**, ou les boutons latéraux de la souris.

- Une page est conservée telle que vous l'avez laissée : y revenir ramène la période et l'aperçu dans l'état où ils étaient, et non une page ouverte à neuf.
- Comme dans un navigateur, choisir une nouvelle page efface ce qui était devant.
- Elles fonctionnent aussi lorsque le volet de navigation est replié, c'est-à-dire au moment où l'aperçu a le plus besoin de largeur.

## Volume d'échanges du marché

Le montant échangé chaque jour sur tout le marché : les montants des indices composites de Shanghai et de Shenzhen additionnés, une barre par séance.

- Seules les journées où tous les marchés retenus ont traité sont conservées, afin qu'un jour férié sur un seul marché ne fasse pas paraître le total en chute libre.
- Une séance encore en cours est écartée. Une journée inachevée ne contient que sa fixation d'ouverture et se dessinerait comme une barre collée à l'axe.
- Ou regarder un seul segment : chaque bourse, chaque marché principal, STAR, ChiNext. Les marchés principaux sont déduits du total de la bourse moins son marché de croissance ; le BSE 50 reste une mesure de composantes.
- Seul le marché des actions A donne un total pour l'ensemble du marché. Avec Hong Kong ou les États-Unis, la page est retirée de la navigation.

## Chandeliers

Les chandeliers d'un instrument : quotidiens, hebdomadaires ou mensuels, dessinés de quatre façons, avec ses moyennes et son volume en dessous.

- **Granularité** décide de la durée que couvre un chandelier : un jour, une semaine ou un mois. La changer relance la récupération, car les trois sont des séries distinctes sur la source.
- **Type de tracé** décide comment les quatre mêmes prix sont dessinés : chandeliers, barres OHLC, ligne de clôture ou aire de clôture. Passer de l'un à l'autre ne récupère rien.
- **Animation** est soit l'arrivée des chandeliers l'un après l'autre jusqu'à ce que tout l'intervalle soit tracé, soit une fenêtre fixe qui avance. C'est la seconde qui garde le chandelier assez large pour être lu sur un intervalle long, et cette largeur est le réglage **Fenêtre**.
- Les moyennes mobiles MA5, MA10 et MA20 peuvent être superposées aux chandeliers ; le panneau de volume en dessous peut être désactivé, et le panneau de prix reprend la place.
- Une semaine ou un mois encore en cours est laissé de côté. Un chandelier fait de trois jours n'est pas une semaine.
- Chaque marché est lu sur sa série ajustée : un jour de division n'est donc pas dessiné comme une baisse, et un dividende non plus.

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




## Course des capitalisations

Les quinze plus grandes sociétés d'un marché en barres horizontales classées par capitalisation,
l'ordre changeant jusqu'à la dernière image. Échantillonnage mensuel.

- **Le classement est refait à chaque période.** La récupération demande d'abord à la source le
  classement du jour par capitalisation, en retient les deux cents premières comme plateau, et y
  ajoute les valeurs lourdes qui y figuraient et en sont sorties ; chaque période affiche ensuite
  les quinze plus grandes de ce plateau. Les membres entrent et sortent donc réellement — 2016,
  c'était le pétrole et les banques ; 2026 y a ajouté 茅台, 宁德时代 et 工业富联. Un plateau écrit
  dans le programme avait manqué une société entrée en bourse et aussitôt propulsée en tête ; le
  plateau est désormais demandé, non mémorisé.
- **Une capitalisation passée est calculée** : la capitalisation du jour multipliée par le rapport
  de prix ajusté de la période. Une augmentation de capital ou un fractionnement s'annule dans la
  série ajustée ; un dividende non — il est réinvesti, donc la valeur passée d'un gros
  distributeur ressort basse. Seul le chiffre de la dernière image vient directement de la source.
- **Une société pas encore cotée grandit à partir de rien** : les valeurs cotées en 2018 montent
  depuis la ligne de base le jour de leur entrée, sans occuper de place à l'avance.
- **L'intervalle est le mois, pas le jour** — cent vingt périodes sur dix ans, douze sur un an, et
  l'en-tête de l'image compte des mois. Un classement par capitalisation est une grandeur lente, et
  un échantillon mensuel obtient tout l'historique en une requête.
- **Chaque marché a ses propres quinze.** Les trois ne sont jamais mélangés : leur monnaie n'est
  pas la même. Hong Kong et New York gardent un plateau fixe, faute de classement accessible à
  cette application.





## Prime A/H

De combien la cotation continentale d'une société dépasse sa cotation hongkongaise, pour les
sociétés cotées des deux côtés — mois après mois, en barres qui se dépassent.

- **Prime = cours A ÷ (cours H × HKD/CNY) − 1.** Rien n'est calculé ici : les deux jambes sont des
  cours réellement payés au même instant, et c'est pourquoi cette page est la seule à récupérer des
  cours **non ajustés**. Une série ajustée vers l'arrière gonfle les cours récents, et deux marchés
  ajustés séparément ne se comparent pas — l'action A d'ICBC s'affiche à 8,28 et la série ajustée
  annonce 13,34, ce qui transforme une prime de +26 % en +245 %.
- **Le même écart s'écrit dans les deux sens.** Cette page donne A contre H, la forme usuelle :
  +194 % signifie que l'action continentale vaut près du triple de l'action hongkongaise. Certains
  services affichent le même chiffre à l'envers (溢价(H/A)) et donnent −66 % pour 新华制药 le même
  jour. C'est le même fait (1 ÷ (1 − 0,66) − 1 = 1,94) : pas un autre cours, pas une erreur.
- **L'image trace les quinze plus chères**, donc les barres poussent vers la droite — la
  quinzième portait encore plus de vingt pour cent. Seules deux des soixante-neuf vont dans l'autre
  sens, leur action H au-dessus de l'action A, et toutes deux finissent en bas de liste, hors champ.
- **Plus la période est longue, moins de sociétés sont retenues.** Soixante-neuf doubles cotations
  connues sont candidates, mais seules celles dont les deux jambes couvrent toute la période sont
  tracées : une cotation hongkongaise de moins de deux ans est écartée.
- **Échantillonnage mensuel.** « Le plus long » fait environ neuf ans, la limite venant de la série
  de change qui ne remonte qu'à 2016. Les trois jambes closent leur mois à des dates différentes :
  on regroupe par mois calendaire et on prend le dernier cours du mois, plutôt que d'intersecter
  sur la date.
- **La liste est intégrée.** Aucune des deux sources ne répond à « quelles cotations continentales
  ont aussi une cotation à Hong Kong ». En revanche elle est vérifiable : chaque paire a été relue
  depuis la source le 2026-10-02, et 海通证券 est ce que cette vérification a retiré (actions H
  radiées après la fusion dans 国泰海通).

## Jours extrêmes

Un instrument, et les jours où il a le plus bougé — des barres horizontales classées par
ampleur. **Les lignes de ce tableau sont des jours, pas des entreprises**, ce qu'aucune autre page
ici ne fait : la valeur d'une ligne est le mouvement de ce jour par rapport à la clôture du jour de
cotation précédent, et une fois ce jour passé la valeur ne change plus jamais.

- **Le mouvement est la variation du cours de clôture ajusté.** Ajusté, parce qu'un jour de
  détachement de dividende n'est pas un krach : le cours baisse du montant du dividende ce matin-là,
  et une série non ajustée placerait ce jour en tête des plus grandes baisses de l'histoire, alors
  que personne n'a rien perdu.
- **Classé par ampleur, pas par signe.** −7,7 % et +8,1 % sont des mouvements de même taille et se
  tiennent donc côte à côte ; classer les valeurs signées mettrait chaque baisse sous chaque hausse.
  Les barres poussent donc des deux côtés : **une hausse vers la droite, en rouge ; une baisse vers
  la gauche, en vert**.
- **Un jour n'est classé qu'une fois arrivé.** Les vingt-quatre plus grands mouvements de la période
  sont les candidats et l'image en dessine les quinze plus grands ; un jour ne participe pas avant sa
  propre date, donc le tableau se remplit au fil des années au lieu d'être plein dès le début.
- **Il y a un seul instrument, l'un des indices larges du marché courant** (dans le marché A :
  le composite de Shanghai, le composant de Shenzhen, le CSI 300 et ainsi de suite). Changer de
  marché change toute la liste ; changer d'instrument ou de période ne fait qu'enregistrer une
  préférence — rien n'est chargé avant d'avoir pressé 取数.
- **La période la plus longue est d'environ trente-cinq ans**, c'est la limite de la source : une
  requête porte environ 640 barres quotidiennes et le retour en arrière en fait vingt au plus. Une
  période de moins de soixante jours de cotation est refusée — le plus grand jour d'un mois calme
  n'est pas un fait qui mérite un tableau.
- **La date en haut de l'image est l'axe du temps**, la barre dessous est la progression. La ligne
  d'en-tête porte la période, le nombre de jours de cotation et le nombre de jours candidats.

## Couloirs de devises

Une ligne par paire, et **la ligne est le couloir lui-même** : une extrémité est le niveau le
plus bas que la paire a connu dans la période choisie, l'autre le plus haut, et le repère est le
cours actuel. Ce tableau n'est donc pas comme les autres — ailleurs la longueur d'une barre dit
*combien*, ici la ligne occupe toute la largeur à chaque image, et ce qui bouge est le repère, avec
le couloir autour de lui.

- **Le couloir s'élargit.** Ses murs sont le plus bas et le plus haut **jusqu'ici**, pas ceux de
  toute la période. Un mois qui va plus loin que tous ceux d'avant pousse l'un des deux vers
  l'extérieur, et une paire à 100 % est au plus cher qu'elle ait jamais été — pas à une limite.
- **Chaque paire est mesurée à sa propre fourchette.** 157,92 sur USD/JPY et 1,1245 sur EUR/USD ne
  sont pas deux points d'une même échelle ; c'est la normalisation qui permet à six paires de tenir
  sur une image. Le prix à payer : un couloir étroit et un couloir large se ressemblent — d'où les
  deux bornes imprimées sous chaque ligne.
- **Bougies mensuelles, non ajustées.** Une devise n'a ni dividende ni split à ajuster, et la page
  prend le même chemin brut dans la source que la page A+H.
- **La couverture diffère, et c'est pourquoi il y a deux listes** : USD/CNY remonte à 2005, les cinq
  autres paires du renminbi à 2016 ; les grands cross commencent tous en 2005-07 et portent 325 mois.
  Sur un seul tableau, on lirait la date à laquelle la source a commencé à coter chaque paire.
- **Le réglage de marché ne s'applique pas ici** : une paire de devises n'appartient à aucune Bourse,
  et le tableau est le même quel que soit le marché en vigueur.
- La période la plus longue est d'environ vingt ans, la couverture mensuelle de la source ; moins de
  douze mois est refusé — c'est quelques semaines de mouvement, pas un couloir.

## Course des indices

Une ligne par indice, et la ligne est **le chemin parcouru par cet indice depuis son propre
premier mois dans la période** — pas son niveau. 3 800 au Shanghai Composite et 5 700 au S&P 500 ne
sont pas deux points d'une même échelle ; dessiner des niveaux ferait un tableau sur l'endroit où
chaque indice a commencé à compter.

- **Un indice qui arrive tard n'est pas sur le tableau avant d'arriver.** Le S&P remonte à 1950, le
  Dow seulement à 2009, et l'indice Hang Seng Tech commence en 2020. Il est absent, il ne stationne
  pas à 0,00 % — à ce niveau il se classerait au-dessus de tout indice jamais baissier, et se lirait
  comme un marché où rien ne s'est passé.
- **Bougies mensuelles, non ajustées.** Un indice ne verse pas de dividende, mais la raison est
  l'autre : un ajustement rebase une série, et deux séries rebasées côte à côte ne sont pas
  comparables. La page prend le même chemin brut dans la source que la page A+H.
- **Le réglage de marché ne gouverne pas cette page** : elle lit trois marchés à la fois, et changer
  de marché ne la change pas. On peut prendre les six du continent, les trois de Hong Kong, les trois
  de New York, ou les douze.
- La période la plus longue est bornée par le plafond mensuel de la source — 430 bougies, environ
  trente-cinq ans ; moins de douze mois est refusé : c'est un sprint, pas une course de fond.

## Classes d'actifs

Une ligne par classe d'actifs, et la ligne est **ce que la détention a rapporté** — pas le cours.
Les huit sont des fonds cotés sur une place continentale, achetés avec le même argent, donc
directement comparables.

- **Les dividendes sont réintégrés, et les scissions aussi.** Une obligation et un fonds monétaire
  paient presque entièrement en revenus : le cours du fonds monétaire est passé de 100,161 à
  100,901 en treize ans, soit +0,0 % sans ajustement — ce qui dessinerait en bas du tableau la seule
  ligne ici qui n'a jamais baissé. Un fonds ayant divisé ses parts est plus net encore : l'ETF
  Nasdaq affiche +136 % sans ajustement, alors que l'indice qu'il suit a sextuplé sur la même
  décennie.
- **Volontairement l'inverse de la course des indices.** Un indice ne verse pas de dividende, cette
  page-là est donc laissée telle quelle ; un fonds en verse, celle-ci doit être ajustée. Les deux
  voies ne se mélangent pas.
- **Les deux lignes étrangères portent le change.** Les ETF Nasdaq et Hang Seng sont cotés en yuan :
  la devise est déjà dedans — c'est ce qu'un détenteur continental a réellement obtenu.
- **Les débuts diffèrent.** La ligne la plus ancienne commence en 2012 et le fonds matières
  premières seulement en 2019. Une ligne qui n'a pas encore rejoint la course est absente, pas à
  0,00 %.
- **Le réglage de marché ne régit pas cette page** : les huit sont cotés sur le continent. Moins de
  douze mois est refusé.

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
- Outre 3, 5 et 10 ans et la période la plus longue, la plage peut être **Personnalisée** : indiquez une date de début et une date de fin, puis récupérez les données. Environ 35 ans sont accessibles — la source sert environ 640 jours civils par requête et le parcours en fait vingt au plus.

## Rendement de position

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/position.png)

Un seul achat, conservé des années — un million dans 中国平安 en 2015, par exemple — animé comme ce que la valeur et le rendement ont fait.

- Les noms proposés suivent le marché : en Chine, les actions que l'on dit réellement avoir gardées (Ping An, Moutai, CMB…), à Hong Kong Tencent, HSBC et le Tracker Fund, aux États-Unis Apple, Berkshire et SPY.
- Le capital initial et la période de détention sont à vous ; la période couvre trois, cinq ou dix ans, ou aussi loin que les données remontent (environ treize ans).
- Le rendement est calculé sur des cours rétro-ajustés — dividendes réinvestis, sans frais. L'ajustement rétroactif s'ancre à l'introduction en bourse et cumule les dividendes vers l'avant, si bien que les premières années d'un gros versant ne deviennent jamais négatives, ce que l'ajustement avant peut produire.
- La même plage **Personnalisée** s'applique à la détention : indiquez deux dates, puis récupérez les données. Si le titre a été coté après la date demandée, la détention commence à son premier jour de cotation.

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

- Le curseur d'opacité règle la part des deux couleurs : à 100 %, l'image est la paire choisie, et en dessous le dégradé sombre de la page apparaît par-dessous. C'est ce qui garde une paire claire lisible.

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
