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

- **Votre liste.** La dernière entrée du menu est la liste que vous tenez — indices et actions
  côte à côte, partagée avec les quatre tableaux à roster. Seuls les codes continentaux peuvent
  être additionnés : les transactions sont publiées dans la devise de chaque marché, donc un nom
  de Hong Kong ou de New York est écarté, et la ligne d'état dit combien. Un jour figure sur
  l'axe dès que *n'importe quel* membre a traité ; un membre sans ligne ce jour-là — suspendu, ou
  pas encore coté — n'apporte rien. C'est délibérément l'inverse de la règle des tableaux
  ci-dessus : un indice n'est jamais suspendu, une action si, et supprimer le jour ferait
  ressembler une suspension à un jour sans aucune transaction nulle part. Ce tableau **additionne
  ses entrées** : cliquer sur un nom l'inclut dans le total ou l'en retire, et il s'ouvre sur la
  **première** seulement. La liste est souvent celle des classements, où une douzaine de noms est
  courant ; une douzaine additionnée est un chiffre sur personne.
- **La variation sous un panier** est la moyenne équipondérée des variations quotidiennes propres
  à chaque membre, mesurée contre sa propre clôture précédente. Équipondérée parce qu'une liste
  n'est pas un portefeuille : il n'y a aucune taille de position par laquelle pondérer.
- **Une séance, minute par minute.** La troisième forme est une autre requête : le total cumulé
  de l'ouverture à la clôture d'un seul jour. La source ne garde que les cinq dernières séances,
  donc aucun intervalle n'est proposé — l'image nomme le jour qu'elle a tracé. La courbe s'arrête
  à 15:00, car la demi-heure ajoutée ensuite par le point d'accès est du hors-séance, que le
  chiffre quotidien exclut également. Les quatre cartes sont le total du jour et la part du
  matin, de l'après-midi et de la dernière demi-heure — un graphique de *quand* l'argent a
  circulé, donc trois cartes sur quatre sont des parts et non des montants. Le BSE 50 est le seul
  tableau à renvoyer des minutes sans colonne de transactions ; il est refusé plutôt que compté
  pour rien.

## Chandeliers

Les chandeliers d'un instrument : quotidiens, hebdomadaires ou mensuels — ou par minute pour une journée de bourse précise — dessinés de quatre façons, avec ses moyennes et son volume en dessous.

- **Granularité** décide de la durée que couvre un chandelier : un jour, une semaine ou un mois. La changer relance la récupération, car les trois sont des séries distinctes sur la source.
- **1, 5 et 15 minutes** dessinent une journée de bourse : la séance de l'ouverture à la clôture, sur un axe qui suit l'horloge et retire les quatre-vingt-dix minutes sans cotation, si bien que le matin et l'après-midi se rejoignent sur un filet plutôt que de laisser un tiers du cadre vide. La source ne conserve les bougies par minute que pour Shanghai et Shenzhen, et seulement pour les dernières séances — environ quatre jours à une minute, dix-sept à cinq, cinquante à quinze — donc **Jour de bourse** est une liste des jours encore disponibles, pas un calendrier. En choisir un autre ne fait que redessiner.
- **Type de tracé** décide comment les quatre mêmes prix sont dessinés : chandeliers, barres OHLC, ligne de clôture ou aire de clôture. Passer de l'un à l'autre ne récupère rien.
- **Animation** est soit l'arrivée des chandeliers l'un après l'autre jusqu'à ce que tout l'intervalle soit tracé, soit une fenêtre fixe qui avance. C'est la seconde qui garde le chandelier assez large pour être lu sur un intervalle long, et cette largeur est le réglage **Fenêtre**.
- **Une fenêtre défilante s'ouvre à la fin.** Au début du segment de fermeture la fenêtre s'élargit vers l'arrière jusqu'au premier jour de la plage : l'image sur laquelle l'animation s'arrête est donc la plage entière et non ses dernières dizaines de jours.
- Les moyennes mobiles MA5, MA10 et MA20 peuvent être superposées aux chandeliers ; le panneau de volume en dessous peut être désactivé, et le panneau de prix reprend la place.
- Une semaine ou un mois encore en cours est laissé de côté. Un chandelier fait de trois jours n'est pas une semaine.
- Chaque marché est lu sur sa série ajustée : un jour de division n'est donc pas dessiné comme une baisse, et un dividende non plus.
- **La plage** suit la période : en quotidien 3, 6 ou 12 mois, ou 3, 5 ou 10 ans ; en hebdomadaire 1, 3, 5 ou 10 ans ; en mensuel 3, 5 ou 10 ans, ou le maximum dont la source dispose (environ 13 ans). Une requête ramène environ 640 bougies quotidiennes et la page remonte page par page : dix ans, soit quelque 2 500 bougies, y tiennent.
- **Deux instruments ou plus font de l'image une comparaison.** Les noms de votre liste sont des interrupteurs : activez-en un deuxième et l'image cesse de tracer des chandeliers — les prix de deux instruments n'ont aucun axe à partager — et trace à la place ce que chacun a fait, en pourcentage cumulé. Chaque courbe est nommée à sa propre extrémité avant, avec son avance ou son retard au moment affiché. Sur les périodes en minutes, tous sont tracés le même jour de bourse : **Jour de bourse** liste ceux qu'ils ont en commun, par défaut la séance complète la plus récente, et les courbes partent du **cours de clôture précédent** — le chiffre au bout est donc la variation du jour de chaque instrument.
- **Plusieurs instruments peuvent partager un graphique ou avoir chacun le leur.** Avec **Disposition** sur « un graphique par instrument », chaque instrument occupe un panneau, empilés, avec son propre axe mis à l'échelle de sa propre amplitude, la ligne du zéro restant à l'intérieur ; l'axe des x et les dates sont communs et ne sont tracés qu'une fois, sous le panneau du bas. La vue éclatée en accepte trois : au-delà de trois sélections, les trois premières de la liste sont tracées et les autres sont nommées dans la barre d'état. Passer d'une disposition à l'autre ne recharge rien. Dans les deux cas, le bas du cadre porte une carte par instrument : en gros sa **variation sur la période**, et dessous de combien de points — ou de combien d'argent — il s'est déplacé, le même chiffre que celui affiché au bout de sa courbe.
- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et commentaire sur ce côté d'une vidéo verticale, et les chandeliers et les extrémités des courbes tracés dessous sont masqués sur le téléphone alors qu'ils sont parfaitement lisibles ici. Activée, les deux images que trace cette page vont jusqu'au bord même de l'image : les chandeliers jusque-là, et le nom et le chiffre au bout d'une courbe de comparaison avec eux ; une fenêtre glissante continue de garder ses distances tant qu'elle est une fenêtre, et s'ouvre à la pleine largeur en même temps qu'elle.
- **Une comparaison dit jusqu'à quel jour elle a tracé.** Les périodes en minutes (1, 5 et 15) écrivent deux lignes sous le titre : en haut ce **seul jour de bourse**, en dessous l'**heure que l'image atteint à cet instant** —— elle avance avec l'image minute par minute. Les périodes quotidienne, hebdomadaire et mensuelle n'écrivent que la ligne du haut : le **jour que l'image atteint à cet instant** —— elle avance avec l'image jour après jour. Seules les images à plusieurs instruments ajoutent ce bloc —— l'image d'un seul instrument porte déjà la date de la bougie qu'elle trace dans son en-tête.

## Volume et rotation

Le volume d'un titre face à son taux de rotation, en deux panneaux superposés.

- D'une séance à l'autre, volume et taux de rotation sont proportionnels : les deux panneaux ont donc presque la même forme. À l'intérieur d'une journée, le volume par minute et la rotation cumulée n'ont plus rien de commun, et c'est l'image la plus intéressante.
- La source intrajournalière ne conserve que les dernières séances ; ce mode propose donc celles-là plutôt qu'une date quelconque.
- Les données minute ne sont servies que pour les actions A et Hong Kong ; aux États-Unis ce mode n'est pas proposé.
- En quotidien, la plage est de 1, 3, 6, 12 ou 24 mois, ou de dates de début et de fin à votre choix ; une plage personnalisée s'arrête à environ 900 jours calendaires — ce qu'une requête ramène — et les sélecteurs de date s'arrêtent au même endroit. Le mode intrajournalier propose de choisir un jour parmi les quelques séances disponibles.

## Course de secteurs

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/sector-race.png)

Un ensemble de secteurs ou d'actions, dessiné en barres horizontales qui se dépassent, l'ordre changeant jusqu'à la dernière image.

- Deux mesures : la variation de la période en % et son volume en centaines de millions de yuans. Changer de mesure ne fait que re-teinter les mêmes données ; cela ne relance pas la requête.
- Quatre listes : secteurs Shenwan de niveau 1, thèmes en vue, personnalisée (à cocher) et actions individuelles (ajout par recherche). La liste personnalisée démarre remplie avec les secteurs Shenwan de niveau 1.
- Les listes intégrées suivent le marché : secteurs Shenwan de niveau 1 et thèmes en vue pour les actions A, quatre sous-indices Hang Seng pour Hong Kong, dix ETF sectoriels SPDR pour les États-Unis. Les listes personnalisée et actions existent sur tous les marchés.
- La période peut être de 1, 3, 6, 12 ou 24 mois, ou des dates de début et de fin personnalisées. Un intervalle personnalisé remonte à environ 900 jours — la portée d'une requête — et les sélecteurs de date s'arrêtent là.
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
- La plage est les 12 derniers mois, 3, 5 ou 10 ans, ou **Maximale** — une requête ramène les 180 périodes mensuelles, soit environ quinze ans, et c'est là que cette entrée s'arrête. Des dates de début et de fin à vous sont proposées également.
  pas la même. Hong Kong et New York gardent un plateau fixe, faute de classement accessible à
  cette application.





## Historique de la valeur de marché

La valeur de marché en circulation d'une action jour par jour, avec son cours en dessous sur le même axe temporel. Ou plusieurs entreprises à la fois — une courbe chacune, nommée à son extrémité.

- **La valeur est reconstituée, pas citée.** La source n'a de nombre d'actions historique pour aucun jour. Il vient du taux de rotation, qui est le volume en fraction des actions en circulation — donc `volume ÷ taux de rotation` *est* ce nombre, et la valeur est le cours du jour multiplié par lui.
- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et commentaire sur ce côté d'une vidéo verticale, et un chiffre en dessous est masqué sur le téléphone alors qu'il est parfaitement lisible ici. Activée, les panneaux tracent jusqu'au bord même de l'image et le graphique est aussi large que l'image.

- **Le nombre est une médiane de vingt jours.** Le taux arrive avec deux décimales : un jour apporte environ un pour cent de bruit, alors que le nombre d'actions est un escalier — il bouge à une augmentation de capital ou un rachat et reste plat entre les deux. La médiane laisse la marche au jour où elle a eu lieu.

- **Seules les actions négociées sur ce marché sont comptées.** Celles que l'entreprise cote ailleurs sont exclues : une société à double cotation passe donc sous la « capitalisation totale » des applications de cotation, qui évalue les actions de l'autre marché au cours de celui-ci. L'écart d'ICBC est entièrement fait d'actions H. Les actions encore immobilisées sont exclues aussi.

- **À Hong Kong, le prix est une moyenne négociée.** Ce marché ne sert pas de clôture non ajustée : le prix est le montant divisé par le volume, et le panneau du bas s'appelle « prix moyen des transactions ».

- **New York divise par toutes les actions, pas par celles qui s'échangent.** Son taux est une fraction de toutes les actions de la société, y compris celles des initiés : la courbe est donc une valeur totale et non une valeur en circulation. Le nombre dépasse la valeur en circulation d'une application exactement de la part des initiés — rien chez Apple, 4 % chez NVIDIA, 12 % chez Tesla. Elle remonte jusqu'à 2009, la même profondeur que le continent.

- **Une courbe de dix ans donne l'impression d'être passée par zéro, et ce n'est pas le cas.** L'axe doit contenir le sommet : un segment ancien qui vaut un dixième se tient à quelques pixels de la base — 853 億 pour 五粮液 contre un sommet de 13 097 億, soit moins de sept pour cent de sa hauteur. C'est pourquoi les repères de minimum et de maximum portent leur chiffre : un simple point là-bas se lit comme zéro.

- **Le chiffre chevauche la ligne.** Une étiquette à l'extrémité de chaque ligne nomme l'entreprise et donne la valeur qu'elle atteint à cet instant, et elle suit l'animation : faites glisser la barre et elle part avec la ligne. Avec une entreprise, les deux panneaux en portent une chacun, valeur et cours, et le grand chiffre au-dessus du panneau dit le même nombre ; avec plusieurs, les étiquettes sont en plus ce qui distingue les lignes entre elles.

- Période : un, deux, cinq ou dix ans, ou deux dates à vous.

Comparez plusieurs entreprises à la fois. Avec plus d'une puce cochée, chacune a sa courbe, nommée à son extrémité. Les cours de plusieurs entreprises ne partagent pas d'axe de prix honnête — mettez 贵州茅台 à côté de 京东方A et l'une des deux n'est qu'une ligne plate au ras du bas —, donc le panneau du bas s'efface et tout le cadre va à la valeur de marché. Jusqu'à six ; une septième est refusée plutôt qu'omise en silence, car un graphique fait avec six des sept entreprises cochées répond à une liste que personne n'a choisie.

L'axe des valeurs a deux lectures. L'absolu répond à la question de laquelle vaut le plus ; le rebasement à 100 au premier jour de chacune, à celle qui a le plus progressé, et c'est la seule lisible dès que l'une vaut plusieurs fois l'autre. Dans les deux cas l'axe des dates est l'union de leurs jours, pas l'intersection : l'intersection ramènerait une comparaison de dix ans au seul parcours de la cotation la plus récente.



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
- **N'importe quel instrument coté sur le marché, pas seulement les grands indices.** Tapez un
  code, un nom ou du pinyin dans la recherche : une action particulière et un fonds coté ont autant
  leur place ici qu'un indice, et la liste en dessous n'est qu'un raccourci vers les habituels.
  Changer de marché remplace cette liste et abandonne un instrument d'un autre marché ; choisir un
  instrument ou une période n'enregistre qu'une préférence — rien n'est chargé avant 取数.
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
- **Mensuel, et désormais ajusté.** Un indice ne distribue rien, mais une action verse des
  dividendes et divise ses titres : Apple affiche +193 % sur dix ans sans ajustement et +1183 %
  ajusté, car la ligne non ajustée porte des falaises dont aucun détenteur n'est jamais tombé. Les
  indices n'y changent pas : si l'on demande un ajustement, la source répond à un indice avec les
  mêmes lignes qu'avant, et les douze étaient identiques sur les deux voies. Ce que le tableau porte
  désormais est une différence qu'il vaut mieux énoncer : la ligne d'un indice est un rendement
  **de prix**, car un indice n'est pas une position, celle d'une action est un rendement **total**,
  dividendes et divisions remis dedans.
- **Le réglage de marché ne gouverne pas cette page** : elle lit trois marchés à la fois, et changer
  de marché ne la change pas. On peut prendre les six du continent, les trois de Hong Kong, les trois
  de New York, ou les douze.
- La période la plus longue est bornée par le plafond mensuel de la source — 430 bougies, environ
  trente-cinq ans ; moins de douze mois est refusé : c'est un sprint, pas une course de fond.
- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et une valeur continentale, une de Hong Kong et une de
  New York peuvent y figurer ensemble — ce tableau ne consulte jamais le réglage de marché. Une
  liste pour quatre tableaux : une action ajoutée ici est également proposée dans la course
  d'actifs, dans les replis et dans le taux de réussite. En dessous de trois, le chargement est
  refusé.

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
- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et les trois marchés peuvent s'y mélanger. Une liste pour
  quatre tableaux : une action ajoutée ici est également proposée sur les trois autres ; elle est
  chargée ajustée, exactement comme les huit fonds, si bien que dividendes et divisions sont dans
  le chiffre. En dessous de trois, le chargement est refusé.

## Marché obligataire

Une ligne par indice obligataire, et la barre est une **variation de cours** — ce qui n'est pas
la même chose que ce que la détention a rapporté.

- **Le coupon n'est pas dans le chiffre.** Les neuf lignes sont des indices, et la source ignore le
  paramètre d'ajustement pour un indice : ce qui revient est donc la cotation. Une obligation paie
  l'essentiel de son rendement en coupon, et un coupon n'apparaît jamais dans une cotation : le
  détenteur a gagné plus que ce que montre ce tableau, et d'un montant différent sur chaque ligne.
- **Volontairement l'inverse de la course des classes d'actifs.** Ce tableau-là est tracé sur la
  série ajustée parce qu'un fonds distribue ; celui-ci est laissé tel quel parce qu'un indice ne
  distribue pas. Les deux tableaux ne se lisent pas l'un contre l'autre.
- **Neuf lignes, et la liste est intégrée** plutôt qu'entretenue par vous. Un indice CSI « toutes
  obligations » était souhaité et n'existe pas sur cette source : le code qui y ressemble est
  l'indice des obligations détachables de Shanghai, dont la série mensuelle s'arrête en août 2015,
  et un balayage de tout l'espace de codes d'indices n'a trouvé aucun indice obligataire global.
  Ces places sont allées aux indices de crédit les plus profonds que la source répond.
- **Les débuts diffèrent.** La ligne la plus ancienne commence en 2003-02 et l'indice convertible de
  Shenzhen seulement en 2014-08 : sur un tableau de dix ans, il arrive donc cinq ans plus tard. Une
  ligne qui n'a pas commencé est absente, pas à 0,00 %.
- **Mensuel**, une barre par mois, et le réglage de marché ne régit pas cette page. Moins de douze
  mois est refusé.
- **Commence au premier mois entier de la plage.** La source ne répond qu'en mois entiers, et une
  barre mensuelle *est* ce mois entier : lorsqu'une plage commence au milieu d'un mois, ce mois
  incomplet ne compte pas — le tableau démarre au mois entier suivant. C'est pourquoi « 10 ans »
  trace 119 mois et non 120 : le mois manquant se trouve hors plage. Les deux dates de l'en-tête
  sont celles du début et de la fin réels.
- **Trois groupes** : les neuf, les six obligations simples sans convertibles, et les trois
  convertibles.

## Reculs

Une ligne, c'est **la distance entre une position et son propre sommet** — pas ce qu'elle a
rapporté, mais ce qu'il a fallu endurer pour le rapporter. Les huit mêmes supports que la course
des classes d'actifs, mesurés par rapport à eux-mêmes au lieu de l'être entre eux.

- **La courbe est le sujet.** Partout ailleurs dans cette application, une valeur est dessinée
  comme une longueur, et une longueur ne peut dire que la profondeur de l'eau à cet instant. Une
  profondeur est une forme dans le temps : le creux et la remontée sont deux endroits de la courbe,
  et la distance qui les sépare sur l'image est le nombre de mois écoulés entre eux.
- **Les deux nombres ne montent pas ensemble.** Sur les dix dernières années, le fonds Nasdaq a
  perdu 25,52 % et était revenu à niveau en six mois ; le fonds CSI 500 a perdu 56,07 % et a mis
  quatre-vingt-six mois. Imprimé comme un seul nombre, le second a l'air d'une version aggravée du
  premier — et il ne l'est pas.
- **Une seule échelle de profondeur pour tout le tableau.** Mettre chaque ligne à l'échelle de son
  propre pire ferait des 0,2 % du fonds monétaire un gouffre de la taille des 56 % du CSI 500, sur
  un tableau dont toute la raison d'être est de dire que ces deux-là ne se comparent pas. Cette
  ligne est donc une ligne plate collée à sa ligne de plus-haut — et **cette platitude est précisément
  ce qu'elle dit**.
- **Ajusté, mensuel, et à partir du premier mois propre à chaque support**, pour les raisons que
  donne la course des classes d'actifs : les distributions d'un fonds n'apparaissent jamais dans
  son cours, et un support qui n'arrive qu'en 2019 n'est pas mesuré contre un sommet qu'il n'avait
  pas.
- **Les lignes courent toujours.** Elles sont ordonnées par la distance qui les sépare de leur
  propre sommet — le plus proche de son sommet en haut — et elles échangent leurs places à mesure
  que les mois passent.
- **L'or et le fonds de matières premières étaient encore sous l'eau lors de cette mesure** — le
  tableau signale ce genre de recul comme ouvert, parce que la période s'est terminée avant qu'il
  ne soit réparé.
- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et les trois marchés peuvent s'y mélanger. Une liste pour
  quatre tableaux : une action ajoutée ici est également proposée sur les trois autres ; elle est
  chargée ajustée, exactement comme les huit fonds, si bien que dividendes et divisions sont dans
  le chiffre. En dessous de trois, le chargement est refusé.

Ne dépend pas du réglage de marché : les huit sont cotés sur une place de marché continentale.
Moins de douze mois dans la période est refusé.

## Taux de réussite

Une ligne, c'est **la part des entrées terminées qui ont gagné** — parmi tous les mois où l'on
aurait pu entrer et garder la même durée, la part qui s'est terminée dans le vert. Les huit mêmes
supports que la course des classes d'actifs et le tableau des reculs, notés sur le fait de savoir
si les détenir a fonctionné, non sur ce qu'ils ont rapporté.

- **Une entrée, c'est de la chance ; quatre-vingt-quatre, c'est un taux.** Chaque mois de la
  période est une entrée, et toutes sont gardées la même durée : détenir trois ans sur dix ans,
  c'est quatre-vingt-quatre entrées par ligne, pas une. Elles partagent des mois, et c'est là le
  point : les réduire à trois entrées indépendantes laisserait un taux avec trois observations.
- **Une entrée compte à partir du mois où elle se termine.** Ce qui est acheté dans les trois
  dernières années de la période n'est pas terminé ; compter une entrée non terminée comme une
  perte ferait plier chaque ligne vers le bas à la fin pour la seule raison du calendrier. Le
  tableau commence donc au premier mois où une entrée pouvait se terminer.
- **Une ligne arrive dès que six entrées sont terminées.** Une entrée, c'est 0 % ou 100 %, et
  chacun de ces deux nombres à un bout du classement est un bout qu'elle n'a pas mérité.
- **Ajusté, mensuel, et à partir du premier mois propre à chaque support**, pour les raisons que
  donne la course des classes d'actifs : les distributions d'un fonds n'apparaissent jamais dans
  son cours, et un fonds lancé en 2019 n'a aucune entrée de 2016 à avoir gagnée ou perdue.
- **La durée de détention est le seul nouveau choix de ce tableau.** Un an et cinq ans sur les
  mêmes dix ans sont deux questions différentes avec deux réponses différentes, et les huit lignes
  se réordonnent entre les deux.
- **Les lignes courent toujours.** Elles sont ordonnées par leur taux — le plus souvent en gain
  en haut — et échangent leurs places à mesure que les mois passent.
- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et les trois marchés peuvent s'y mélanger. Une liste pour
  quatre tableaux : une action ajoutée ici est également proposée sur les trois autres ; elle est
  chargée ajustée, exactement comme les huit fonds, si bien que dividendes et divisions sont dans
  le chiffre. En dessous de trois, le chargement est refusé.

Mesuré sur les dix dernières années avec une détention de trois ans : le fonds Nasdaq était en
avance sur ses quatre-vingt-quatre entrées et le fonds de Hong Kong sur quarante pour cent d'entre
elles — deux lignes que la course des classes d'actifs sépare par dix ans de rendement total et que
ce tableau sépare par le fait d'entrer, tout simplement.

Ne dépend pas du réglage de marché : les huit sont cotés sur une place continentale. Moins de douze
mois dans la période est refusé.

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

Acheter un titre à montant et cadence fixes — chaque jour de bourse, chaque semaine ou chaque mois — et voir en animation ce que la discipline a produit. Plusieurs plans peuvent partager le même cadre : une ligne de valeur chacun, avec son gain courant à son extrémité.

- Les instruments viennent de **votre propre liste**, celle que partagent les autres tableaux : cherchez un code ou un nom pour en ajouter un, l'interrupteur de chaque pastille décide s'il figure sur ce cadre, et le × le retire de la liste partagée (et donc des autres tableaux). La rangée en un clic suit le marché — ETF larges et or sur les actions A, fonds indiciels de Hong Kong, SPY, QQQ et GLD aux États-Unis — et une pression ajoute ce nom et le dessine aussitôt.
- **De 2 à 6 plans sur un même cadre.** Chacun verse le même montant à la même cadence, en achetant depuis son propre premier jour de cotation. Seules les lignes de valeur sont tracées : six aplats superposés, c'est de la boue, et à montant et cadence égaux les six lignes de versement tombent exactement l'une sur l'autre — la ligne des versements est donc tracée une seule fois, pour le plan qui a le plus versé, car tracer le plus petit versement ferait paraître les autres meilleurs. L'axe des dates est l'union de leurs jours : une cote plus tardive commence simplement plus tard, et n'est pas présente avant. Six est le plafond — au-delà, la récupération refuse au lieu d'en dessiner quelques-uns — et un instrument d'un autre marché est écarté. Avec plusieurs, le grand chiffre au centre devient le rendement en pourcentage du plan **en tête**, et non son argent : une cote plus tardive a moins versé, et gagner moins n'est pas être le plus mauvais plan.
- **Le chiffre suit la ligne.** Une étiquette à l'extrémité de chaque plan le nomme et donne l'argent qu'il a gagné à cet instant ; elle bouge avec l'animation — tirez la barre et elle suit la ligne. Avec un seul plan, le grand chiffre au centre reste le rendement en pourcentage, et l'étiquette est là tout de même.
- Le montant et la fréquence se règlent librement ; la période fait trois, cinq ou dix ans, ou remonte aussi loin que les données le permettent (environ treize ans).
- Le rendement est calculé sur des clôtures rétro-ajustées, sans frais. Le résultat décrit la série de prix, pas une facture que qui que ce soit aurait pu exécuter.
- Outre 3, 5 et 10 ans et la période la plus longue, la plage peut être **Personnalisée** : indiquez une date de début et une date de fin, puis récupérez les données. Environ 35 ans sont accessibles — la source sert environ 640 jours civils par requête et le parcours en fait vingt au plus.
- **Deux animations.** *Tracer tout l'intervalle* déploie toute la période d'un coup ; *fenêtre glissante* garde une fenêtre d'un nombre fixe de jours de cotation et la fait avancer du début à la fin de la période — le seul moyen de garder lisibles les oscillations d'une longue série quotidienne. La fenêtre ne compte qu'en défilement, et les deux animations lisent **les mêmes données** : en changer ne recharge rien. **L'axe vertical n'est pas rééchelonné par fenêtre** : l'écart entre les deux lignes *est* le résultat d'un plan, et le rééchelonner l'élargirait avec la fenêtre.
- **Une fenêtre défilante s'ouvre à la fin.** Au début du segment de fermeture la fenêtre s'élargit vers l'arrière jusqu'au premier jour de la plage : l'image sur laquelle l'animation s'arrête est donc la plage entière et non ses dernières dizaines de jours.
- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et commentaire sur ce côté d'une vidéo verticale, et un chiffre en dessous est masqué sur le téléphone alors qu'il est parfaitement lisible ici. Activée, une image qui remplit toute la période trace jusqu'au bord même de l'image dès sa première image ; une fenêtre glissante continue de garder ses distances tant qu'elle est une fenêtre, et s'ouvre à la pleine largeur en même temps qu'elle — l'image sur laquelle la vidéo s'arrête est donc toute la période, d'un bord à l'autre.

## Rendement de position

![La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.](media/position.png)

Un achat, conservé — un million du même nom depuis 2015 — animé pour montrer ce que les années ont fait à sa valeur et à sa performance. Plusieurs positions peuvent partager le même cadre : une ligne chacune, avec son gain courant à son extrémité.

- Les positions viennent de **votre propre liste**, celle que partagent les autres tableaux : cherchez un code ou un nom pour en ajouter une, l'interrupteur de chaque pastille décide si elle figure sur ce cadre, et le × la retire de la liste partagée (et donc des autres tableaux). La rangée en un clic suit le marché — 中国平安 et 贵州茅台 pour le continent, 腾讯, 汇丰 et 盈富基金 pour Hong Kong, Apple, Berkshire et SPY pour New York — et une pression ajoute ce nom et le dessine aussitôt.
- **De 2 à 6 positions sur un même cadre.** Chacune est achetée une fois, du même montant, à son propre premier jour de cotation : les lignes sont donc directement comparables, et l'écart entre deux d'entre elles à une date donnée est la réponse à « lequel était le meilleur endroit pour cet argent ». L'axe des dates est l'union de leurs jours : une valeur cotée plus tard commence simplement plus tard, et n'est pas présente avant, au lieu d'être tracée à plat sur le capital. Six est le plafond — au-delà, la récupération refuse au lieu d'en dessiner quelques-unes — et une position d'un autre marché est écartée, car les montants ici sont dans la devise du marché en vigueur.
- **Le chiffre chevauche la ligne.** Une étiquette à l'extrémité de chaque position la nomme et donne le gain en argent à cet instant, et elle suit l'animation : faites glisser la barre et elle part avec la ligne. Avec une position, le grand chiffre du milieu reste le rendement en pourcentage ; avec plusieurs, il devient le gain de la **meneuse**, son nom juste en dessous, et les cartes de fin deviennent une par position au lieu des quatre chiffres qui en décrivent une.
- Le capital initial et la période de détention sont à vous ; la période couvre trois, cinq ou dix ans, ou aussi loin que les données remontent (environ treize ans).
- Le rendement est calculé sur des cours rétro-ajustés — dividendes réinvestis, sans frais. L'ajustement rétroactif s'ancre à l'introduction en bourse et cumule les dividendes vers l'avant, si bien que les premières années d'un gros versant ne deviennent jamais négatives, ce que l'ajustement avant peut produire.
- La même plage **Personnalisée** s'applique à la détention : indiquez deux dates, puis récupérez les données. Si le titre a été coté après la date demandée, la détention commence à son premier jour de cotation.
- **Deux animations.** *Tracer tout l'intervalle* déploie toute la période d'un coup : la forme de la courbe à l'écran est sa forme dans le temps. *Fenêtre glissante* garde une fenêtre d'un nombre fixe de jours de cotation et la fait avancer du début à la fin de la période — c'est le seul moyen de garder lisibles les oscillations d'une longue série quotidienne : étalée sur douze ans, une baisse de trois mois fait deux pixels. La fenêtre ne compte qu'en défilement, et les deux animations lisent **les mêmes données** : en changer ne recharge rien.
- **Une fenêtre défilante s'ouvre à la fin.** Au début du segment de fermeture la fenêtre s'élargit vers l'arrière jusqu'au premier jour de la plage : l'image sur laquelle l'animation s'arrête est donc la plage entière et non ses dernières dizaines de jours.
- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et commentaire sur ce côté d'une vidéo verticale, et un chiffre en dessous est masqué sur le téléphone alors qu'il est parfaitement lisible ici. Activée, une image qui remplit toute la période trace jusqu'au bord même de l'image dès sa première image ; une fenêtre glissante continue de garder ses distances tant qu'elle est une fenêtre, et s'ouvre à la pleine largeur en même temps qu'elle — l'image sur laquelle la vidéo s'arrête est donc toute la période, d'un bord à l'autre.

## Vidéo

L'image est toujours en 9:16. Tout le reste vous appartient.

- La durée change le rythme, elle ne raccourcit pas l'animation : l'ouverture, la croissance des barres et les statistiques finales sont réparties sur la longueur choisie.
- Les marges sont notées par rapport à une image de 1080×1920 puis mises à l'échelle de la résolution d'export ; une mise en page réglée une fois tient à toutes les tailles. La marge gauche détermine aussi où se posent les graduations : trop petite, les chiffres sortent de l'image.
- Les repères de zone sûre délimitent ce qu'une application mobile recouvre de sa propre interface. Ils sont tracés dans l'aperçu et jamais dans un fichier.
- Le titre peut tenir sur plusieurs lignes : appuyez sur Entrée dans le champ du titre pour le couper où vous voulez. S'il ne tient pas sur une ligne, il se replie sur une deuxième, deux au maximum ; ce n'est que si deux ne suffisent pas que la taille cède. Une deuxième ligne décale d'une ligne tout ce qui suit, et le graphique raccourcit d'autant.
- **Le nom et le chiffre au bout d'une courbe s'arrêtent avant l'interface de la plateforme.** Une application mobile place son avatar et ses boutons « j'aime » et commentaire sur le bord droit d'une vidéo verticale ; la zone de tracé s'arrête donc avant le bord droit de l'image, et le point courant d'une courbe — avec le nom et le chiffre qui l'accompagnent — se pose à gauche de cette bande. Le graphique est plus étroit que l'image, et c'est pourquoi.

- Tout est gratuit jusqu'à la dernière étape : charger les données, lire l'animation, enregistrer une image de couverture. **Exporter** est le seul endroit qui demande un abonnement mensuel, et un clic dit ce qu'il achète et ce qu'il coûte. Il se renouvelle jusqu'à ce que vous le résiliiez dans le Microsoft Store.

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

- **Chaque image porte aussi un nom sur son fond : le filigrane.** Il est activé par défaut, il dit « 周期留白 » jusqu'à ce que vous le changiez, et le libellé vous appartient. Il se répète en diagonale sur toute l'image, dessiné **sous** les données, donc il ne cache rien ; l'aperçu, la vidéo exportée et l'image de couverture le portent également. Laissé vide, il reprend le nom par défaut — pour ne rien porter du tout, désactivez-le. L'interrupteur est activé par défaut parce qu'une vidéo est publiée quelque part qui ne dit rien d'où elle a été faite.

- Retirer le filigrane est l'une des deux choses que l'abonnement achète. Tant qu'il n'y en a pas, l'interrupteur reste activé et ne peut pas être déplacé — et c'est exactement ce que portera chaque image, si bien que l'aperçu et le fichier ne se contredisent jamais.


- **L'aspect de la marque vous appartient aussi.** La police est n'importe quelle police installée sur cette machine — chaque entrée de la liste est écrite dans la police qu'elle nomme —, la couleur est celle que donne le sélecteur, et l'intensité est la part de cette couleur utilisée : 10% par défaut, jusqu'à 40%, et même au maximum elle est dessinée sous les données. Ces trois réglages valent pour l'aperçu, la vidéo exportée et l'image de couverture.

- **Tant qu'il n'y a pas d'abonnement, ce curseur reste à 40 %.** Baisser l'intensité va avec le retrait de la marque : une application non abonnée dessine chaque image à pleine intensité et le curseur ne peut pas en bouger. Les 10 % plus haut sont la valeur de départ une fois l'abonnement en place.
- Le libellé par défaut ne suit pas la langue de l'interface : un filigrane est une signature, et une signature qui changerait avec la langue en serait une différente sur chaque machine.

## Les données, et ce qu'elles ne diront pas

Les cours viennent des points d'accès publics de Tencent Finance, et l'image cite toujours la source. Ces vidéos décrivent ce qui s'est déjà échangé. Elles sont fournies à titre indicatif et ne constituent pas un conseil en investissement.

- Les montants sont convertis en centaines de millions de yuans, et le volume passe à une unité plus grande dès que les chiffres l'exigent, pour que l'axe reste lisible.
- Les montants sont convertis en centaines de millions — de yuans sur le continent et à Hong Kong, de dollars aux États-Unis. Chaque marché garde sa propre devise.
- Une plage plus longue que ce qu'une requête peut ramener est refusée plutôt que tronquée en silence : environ 900 jours calendaires en quotidien, environ quinze ans sur la page Chandeliers, qui remonte page par page, et toute l'historique en mensuel. Tronquer en silence est le pire résultat — ce qui disparaît alors, c'est le **début**, et un graphique amputé de ses premières années est un graphique plus court qui a l'air parfaitement normal.

## Mise à jour

Quand le Microsoft Store propose une version plus récente, un bouton **Mettre à jour** apparaît à côté de Paramètres dans le volet de navigation ; un clic l'installe.

- Il n'apparaît que si le Store a réellement une version plus récente. Une version de développement ou installée à côté ne le voit jamais, et c'est normal.
- L'application se ferme pendant l'installation et redémarre sur la nouvelle version, et le bouton disparaît. Si un export est en cours, elle demande d'abord.
- Si l'installation échoue, la raison est donnée — Wi-Fi uniquement, batterie trop faible — et la mise à jour peut aussi être installée depuis le Microsoft Store.

## Un problème ?

Écrivez à gaqo@outlook.com en disant ce que vous faisiez et ce que vous attendiez à la place. Le numéro de version figure sur la page des paramètres.
