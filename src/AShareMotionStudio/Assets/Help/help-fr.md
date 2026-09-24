# AShare Motion Studio

Cette application transforme des indicateurs du marché des actions A en vidéos verticales pour téléphone. Vous choisissez une période, vous regardez l'aperçu jusqu'à ce qu'il se lise bien, puis vous exportez un MP4. Rien d'autre n'est à installer.

## Volume d'échanges du marché

Le montant échangé chaque jour sur tout le marché : les montants des indices composites de Shanghai et de Shenzhen additionnés, une barre par séance.

- Seules les journées où tous les marchés retenus ont traité sont conservées, afin qu'un jour férié sur un seul marché ne fasse pas paraître le total en chute libre.
- Une séance encore en cours est écartée. Une journée inachevée ne contient que sa fixation d'ouverture et se dessinerait comme une barre collée à l'axe.
- L'option Pékin ajoute l'indice BSE 50, qui ne couvre que ses composantes et non la bourse entière. C'est une autre mesure, et une plus petite.

## Volume d'un titre

Le volume d'un titre face à son taux de rotation, en deux panneaux superposés.

- D'une séance à l'autre, volume et taux de rotation sont proportionnels : les deux panneaux ont donc presque la même forme. À l'intérieur d'une journée, le volume par minute et la rotation cumulée n'ont plus rien de commun, et c'est l'image la plus intéressante.
- La source intrajournalière ne conserve que les dernières séances ; ce mode propose donc celles-là plutôt qu'une date quelconque.

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
