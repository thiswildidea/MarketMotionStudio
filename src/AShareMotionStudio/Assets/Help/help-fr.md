# AShare Motion Studio

Cette application transforme des indicateurs du marché des actions A en vidéos verticales pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4. Rien d'autre n'est à installer.

## Volume d'échanges du marché

Le montant échangé chaque jour sur tout le marché : les montants des indices composites de Shanghai et de Shenzhen additionnés, une barre par séance.

- Seules les journées où tous les marchés retenus ont traité sont conservées, afin qu'un jour férié sur un seul marché ne fasse pas paraître le total en chute libre.
- Une séance encore en cours est écartée. Une journée inachevée ne contient que sa fixation d'ouverture et se dessinerait comme une barre collée à l'axe.
- Ou regarder un seul segment : chaque bourse, chaque marché principal, STAR, ChiNext. Les marchés principaux sont déduits du total de la bourse moins son marché de croissance ; le BSE 50 reste une mesure de composantes.

## Volume et rotation

Le volume d'un titre face à son taux de rotation, en deux panneaux superposés.

- D'une séance à l'autre, volume et taux de rotation sont proportionnels : les deux panneaux ont donc presque la même forme. À l'intérieur d'une journée, le volume par minute et la rotation cumulée n'ont plus rien de commun, et c'est l'image la plus intéressante.
- La source intrajournalière ne conserve que les dernières séances ; ce mode propose donc celles-là plutôt qu'une date quelconque.

## Course de secteurs

Un ensemble de secteurs ou d'actions, dessiné en barres horizontales qui se dépassent, l'ordre changeant jusqu'à la dernière image.

- Deux mesures : la variation de la période en % et son volume en centaines de millions de yuans. Changer de mesure ne fait que re-teinter les mêmes données ; cela ne relance pas la requête.
- Quatre listes : secteurs Shenwan de niveau 1, thèmes en vue, personnalisée (à cocher) et actions individuelles (ajout par recherche). La liste personnalisée démarre remplie avec les secteurs Shenwan de niveau 1.
- La période peut être de 1, 3, 6 ou 12 mois, ou des dates de début et de fin personnalisées.
- Une liste a un nombre minimum et maximum d'entrées — trop peu, ce n'est pas une course ; trop, c'est un fouillis.

## Matrice des rendements

Des barres mensuelles disposées en grille : le mode année montre la saisonnalité d'un instrument sur dix ans, le mode comparaison met plusieurs instruments côte à côte pour montrer la rotation.

- Mode année : choisissez un instrument (recherche ou un indice large prédefini) ; la plage va de 1 à 10 ans ou tous. Une requête renvoie dix ans de barres mensuelles.
- Mode comparaison : 2 à 14 instruments d'une liste (secteurs de niveau 1 / thèmes / indices larges / personnalisée / actions) côte à côte, sur 6 à 48 mois.
- La grille s'allume case par case dans l'ordre du temps ; la fin présente le meilleur et le pire mois de la plage, entre autres statistiques.
- Les données mensuelles couvrent une décennie d'un coup, il n'y a donc pas de limite quotidienne ici — mais trop d'instruments débordent du cadre.

## Calendrier des hausses et baisses

Toute action ou tout indice chinois, sa hausse ou baisse quotidienne disposée en cellules de calendrier par mois : rouge à la hausse, vert à la baisse.

- Recherche par code, nom ou pinyin ; les préréglages sont des indices larges. Actions et indices chinois uniquement.
- La liste de favoris est partagée avec la page d'actions de l'application — un favori ajouté des deux côtés apparaît des deux côtés.
- La période est de 1, 3, 6 ou 12 mois, ou personnalisée ; un instrument seul reste soumis à la limite d'environ 640 jours calendaires.
- Les statistiques finales donnent le nombre de séances en hausse et en baisse.

## Vidéo

L'image est toujours en 9:16. Tout le reste vous appartient.

- La durée change le rythme, elle ne raccourcit pas l'animation : l'ouverture, la croissance des barres et les statistiques finales sont réparties sur la longueur choisie.
- Les marges sont notées par rapport à une image de 1080×1920 puis mises à l'échelle de la résolution d'export ; une mise en page réglée une fois tient à toutes les tailles. La marge gauche détermine aussi où se posent les graduations : trop petite, les chiffres sortent de l'image.
- Les repères de zone sûre délimitent ce qu'une application mobile recouvre de sa propre interface. Ils sont tracés dans l'aperçu et jamais dans un fichier.

## Où vont les vidéos

Les exports sont écrits dans un dossier que vous choisissez par un sélecteur. Tant qu'aucun n'est choisi, le premier export le demande puis le retient ; les paramètres permettent de le changer ou de l'oublier.

## Les données, et ce qu'elles ne diront pas

Les cours viennent des points d'accès publics de Tencent Finance, et l'image cite toujours la source. Ces vidéos décrivent ce qui s'est déjà échangé. Elles sont fournies à titre indicatif et ne constituent pas un conseil en investissement.

- Les montants sont convertis en centaines de millions de yuans, et le volume passe à une unité plus grande dès que les chiffres l'exigent, pour que l'axe reste lisible.
- Une période de plus de 640 jours civils environ est refusée plutôt que tronquée en silence, car c'est tout ce qu'une requête à la source renvoie.

## Un problème ?

Écrivez à gaqo@outlook.com en disant ce que vous faisiez et ce que vous attendiez à la place. Le numéro de version figure sur la page des paramètres.
