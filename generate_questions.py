import json, random
from pathlib import Path

SOURCE = "Découvrir le Canada — guide d’étude officiel d’IRCC"
MODULES = [
 ("droits", "Droits et responsabilités", [
  ("Quelles sont les deux langues officielles du Canada?", "Le français et l’anglais", ["Le français seulement", "L’anglais et l’espagnol", "Le français et l’inuktitut"], "Le français et l’anglais ont un statut officiel égal au Parlement et au gouvernement fédéral."),
  ("Que signifie la primauté du droit?", "Tous, y compris les gouvernements, sont soumis à la loi", ["Le gouvernement peut ignorer les tribunaux", "Seuls les citoyens sont soumis à la loi", "La police rédige toutes les lois"], "La loi s’applique aux citoyens, aux institutions et aux gouvernements."),
  ("Laquelle est une responsabilité liée à la citoyenneté?", "Faire partie d’un jury lorsqu’on est appelé", ["Posséder une maison", "Parler trois langues", "Travailler pour le gouvernement"], "Servir comme juré lorsqu’on est convoqué est une responsabilité civique."),
  ("Quel droit permet de choisir ses représentants?", "Le droit de vote", ["Le droit de propriété", "Le droit de voyager", "Le droit à un emploi"], "Les citoyens canadiens adultes peuvent participer aux élections en votant."),
  ("Quelle liberté protège la possibilité d’exprimer ses idées?", "La liberté d’expression", ["La liberté de taxation", "La liberté administrative", "La liberté de résidence"], "La liberté de pensée, de croyance, d’opinion et d’expression est fondamentale."),
  ("Comment la loi considère-t-elle les femmes et les hommes?", "Ils sont égaux devant la loi", ["Les droits dépendent de la province", "Les hommes ont priorité", "L’égalité ne concerne que le travail"], "L’égalité entre les femmes et les hommes est une valeur et un droit fondamentaux."),
 ]),
 ("identite", "Qui sommes-nous?", [
  ("Quels sont les trois principaux peuples autochtones reconnus?", "Premières Nations, Inuit et Métis", ["Acadiens, Inuit et Loyalistes", "Métis, Vikings et Canadiens", "Premières Nations, Québécois et Inuit"], "La Constitution reconnaît les Premières Nations, les Inuit et les Métis."),
  ("Que signifie le mot Inuit?", "Le peuple", ["Le Nord", "Les chasseurs", "La neige"], "Inuit signifie « le peuple » en inuktitut."),
  ("Qui sont les Métis?", "Un peuple autochtone distinct issu notamment d’unions entre Autochtones et Européens", ["Tous les nouveaux immigrants", "Des colons britanniques seulement", "Une nation européenne"], "Les Métis forment un peuple autochtone distinct avec sa propre identité et culture."),
  ("Qu’est-ce que l’Acadie historique?", "Une colonie française établie dans les Maritimes", ["La première capitale du Canada", "Un territoire du Grand Nord", "Une colonie espagnole"], "Les Acadiens sont les descendants de colons français établis dans les Maritimes dès 1604."),
  ("Qui sont les Québécois?", "Les habitants du Québec, majoritairement francophones et porteurs d’une identité particulière", ["Uniquement les personnes nées en France", "Tous les francophones du monde", "Seulement les habitants de Québec-ville"], "Le guide reconnaît la contribution particulière du Québec et de sa majorité francophone."),
  ("Que reconnaît le multiculturalisme canadien?", "La diversité culturelle comme caractéristique de l’identité canadienne", ["Une culture unique obligatoire", "L’interdiction des traditions", "La séparation des provinces"], "Le multiculturalisme valorise la diversité tout en respectant les lois et valeurs communes."),
 ]),
 ("histoire", "Histoire du Canada", [
  ("Qui furent les premiers Européens connus à atteindre le Canada?", "Les Vikings", ["Les Romains", "Les Espagnols", "Les Portugais"], "Des Vikings ont établi une présence à L’Anse aux Meadows vers l’an 1000."),
  ("Qui a exploré le fleuve Saint-Laurent en 1534?", "Jacques Cartier", ["Samuel de Champlain", "John Cabot", "James Cook"], "Jacques Cartier a pris possession du territoire au nom du roi de France."),
  ("Qui a fondé Québec en 1608?", "Samuel de Champlain", ["Jacques Cartier", "Louis Riel", "John A. Macdonald"], "Champlain a établi Québec, premier établissement permanent français important."),
  ("Quelle bataille de 1759 fut décisive pour la Nouvelle-France?", "La bataille des plaines d’Abraham", ["La bataille de Vimy", "La bataille de Queenston Heights", "La bataille de Dieppe"], "La victoire britannique aux plaines d’Abraham a mené à la fin du régime français."),
  ("En quelle année la Confédération canadienne a-t-elle été créée?", "1867", ["1759", "1812", "1982"], "L’Acte de l’Amérique du Nord britannique est entré en vigueur le 1er juillet 1867."),
  ("Qui fut le premier premier ministre du Canada?", "Sir John A. Macdonald", ["Sir Wilfrid Laurier", "George-Étienne Cartier", "Alexander Mackenzie"], "Sir John A. Macdonald a dirigé le premier gouvernement du Dominion du Canada."),
 ]),
 ("moderne", "Le Canada moderne", [
  ("Quelle bataille de la Première Guerre mondiale est un symbole national important?", "La crête de Vimy", ["Waterloo", "Gettysburg", "Yorktown"], "La victoire canadienne à Vimy en 1917 est souvent associée à l’affirmation nationale."),
  ("Que commémore le jour du Souvenir?", "Les sacrifices des Canadiens ayant servi en temps de guerre", ["La Confédération", "La fête de la Reine", "La première élection"], "Le 11 novembre, on honore ceux qui ont servi et donné leur vie."),
  ("Quand les femmes ont-elles obtenu le droit de vote fédéral de façon générale?", "En 1918", ["En 1867", "En 1949", "En 1982"], "La plupart des citoyennes canadiennes de 21 ans et plus ont obtenu le vote fédéral en 1918."),
  ("Quand Terre-Neuve-et-Labrador a-t-elle rejoint le Canada?", "En 1949", ["En 1867", "En 1873", "En 1999"], "Terre-Neuve-et-Labrador est devenue la dixième province en 1949."),
  ("Quand le Nunavut a-t-il été créé?", "En 1999", ["En 1867", "En 1949", "En 1982"], "Le Nunavut est devenu un territoire distinct le 1er avril 1999."),
  ("Quel document de 1982 protège les droits et libertés?", "La Charte canadienne des droits et libertés", ["La Proclamation royale", "Le Traité de Paris", "L’Acte de Québec"], "La Charte fait partie de la Constitution rapatriée en 1982."),
 ]),
 ("gouvernement", "Gouvernement et démocratie", [
  ("Quels trois termes décrivent le système politique canadien?", "Monarchie constitutionnelle, démocratie parlementaire et État fédéral", ["République, État unitaire et démocratie directe", "Monarchie absolue, confédération et empire", "République présidentielle et État fédéral"], "Le Canada combine la Couronne, un Parlement démocratique et un partage fédéral des pouvoirs."),
  ("Qui est le chef d’État du Canada?", "Le souverain", ["Le premier ministre", "Le gouverneur général", "Le juge en chef"], "Le souverain est le chef d’État; le gouverneur général le représente au niveau fédéral."),
  ("Qui est le chef du gouvernement fédéral?", "Le premier ministre", ["Le souverain", "Le président du Sénat", "Le gouverneur général"], "Le premier ministre dirige le gouvernement et choisit les membres du Cabinet."),
  ("Quelles sont les trois parties du Parlement?", "Le souverain, le Sénat et la Chambre des communes", ["Le Cabinet, les tribunaux et la police", "Les provinces, les villes et le fédéral", "La Chambre, les maires et les juges"], "Une loi fédérale doit franchir les étapes parlementaires et recevoir la sanction royale."),
  ("Quel ordre de gouvernement gère notamment la défense nationale?", "Le gouvernement fédéral", ["Les municipalités", "Les commissions scolaires", "Les gouvernements municipaux et territoriaux uniquement"], "La défense, la politique étrangère et la monnaie relèvent notamment du fédéral."),
  ("Quel ordre de gouvernement est responsable notamment de l’éducation?", "Les provinces et territoires", ["Le gouvernement fédéral seulement", "Les municipalités seulement", "Le Sénat"], "L’éducation et la santé relèvent principalement des provinces et territoires."),
 ]),
 ("elections", "Élections fédérales", [
  ("Quel âge minimal faut-il avoir pour voter à une élection fédérale?", "18 ans", ["16 ans", "19 ans", "21 ans"], "Il faut être citoyen canadien et avoir au moins 18 ans le jour du scrutin."),
  ("Que choisit-on directement lors d’une élection fédérale?", "Un député pour sa circonscription", ["Le premier ministre directement", "Le gouverneur général", "Les sénateurs"], "Les électeurs choisissent leur député; le chef qui peut former le gouvernement devient normalement premier ministre."),
  ("Qu’est-ce qu’une circonscription électorale?", "Une zone géographique représentée par un député", ["Un tribunal électoral", "Un parti politique", "Une réunion du Cabinet"], "Chaque circonscription élit un député à la Chambre des communes."),
  ("Le vote au Canada est-il secret?", "Oui, personne ne peut exiger de savoir pour qui vous avez voté", ["Non, il est public", "Seulement aux élections provinciales", "Seulement pour les nouveaux citoyens"], "Le secret du vote protège la liberté de choix de chaque électeur."),
  ("Quel organisme administre les élections fédérales?", "Élections Canada", ["Statistique Canada", "La GRC", "Le Sénat"], "Élections Canada est un organisme indépendant et non partisan."),
  ("Qu’est-ce qu’un gouvernement minoritaire?", "Le parti au pouvoir détient moins de la moitié des sièges", ["Aucun député n’est élu", "Le Sénat gouverne", "Le parti au pouvoir a tous les sièges"], "Un gouvernement minoritaire doit obtenir l’appui d’autres députés pour faire adopter certaines mesures."),
 ]),
 ("justice", "Justice et lois", [
  ("Quel principe s’applique à une personne accusée d’un crime?", "Elle est présumée innocente jusqu’à preuve du contraire", ["Elle doit prouver son innocence", "Elle perd automatiquement ses droits", "La police décide seule de sa culpabilité"], "La présomption d’innocence est un principe fondamental de la justice canadienne."),
  ("Quel est le rôle principal des tribunaux?", "Régler les différends et appliquer la loi", ["Créer les partis politiques", "Percevoir les taxes municipales", "Élire le gouvernement"], "Les tribunaux interprètent la loi et rendent des décisions impartiales."),
  ("Quel est le plus haut tribunal du pays?", "La Cour suprême du Canada", ["La Cour fédérale", "Le Sénat", "La Couronne"], "La Cour suprême est la juridiction d’appel finale du Canada."),
  ("Que fait la police?", "Elle maintient l’ordre et fait respecter la loi", ["Elle adopte les lois", "Elle prononce toutes les peines", "Elle dirige les élections"], "La police protège le public et enquête sur les infractions, sous l’autorité de la loi."),
  ("Peut-on demander l’aide de la police sans crainte au Canada?", "Oui, la police est là pour aider et protéger", ["Seulement si l’on est propriétaire", "Seulement avec un avocat", "Non, jamais directement"], "Toute personne peut demander l’aide de la police; les services d’urgence sont accessibles par le 911."),
  ("Qu’est-ce que l’habeas corpus protège?", "Le droit de contester une détention illégale", ["Le droit automatique à un emploi", "Le droit de ne jamais payer d’impôt", "Le droit de voter deux fois"], "Cette tradition juridique protège contre l’emprisonnement arbitraire."),
 ]),
 ("symboles", "Symboles canadiens", [
  ("Quel symbole figure au centre du drapeau canadien?", "La feuille d’érable", ["Le castor", "La fleur de lys", "L’ours polaire"], "Le drapeau rouge et blanc à la feuille d’érable a été adopté en 1965."),
  ("Quel est l’hymne national du Canada?", "Ô Canada", ["God Save the King", "The Maple Leaf Forever", "Canada the Brave"], "Ô Canada a été proclamé hymne national en 1980."),
  ("Quel animal est un symbole officiel ancien du Canada?", "Le castor", ["Le lion", "Le bison uniquement", "Le caribou uniquement"], "Le castor est associé à l’histoire du commerce des fourrures et au développement du pays."),
  ("Quelles sont les couleurs nationales du Canada?", "Le rouge et le blanc", ["Le bleu et le blanc", "Le vert et l’or", "Le rouge et le bleu"], "Le rouge et le blanc sont les couleurs nationales depuis 1921."),
  ("Que représente la Couronne au Canada?", "L’État, son autorité et la continuité du gouvernement", ["Un parti politique", "Une entreprise privée", "Une province particulière"], "La Couronne est un symbole de l’État et du gouvernement constitutionnel."),
  ("Quel sport est officiellement le sport national d’hiver?", "Le hockey sur glace", ["Le soccer", "Le baseball", "Le curling"], "Le hockey est le sport national d’hiver; la crosse est le sport national d’été."),
 ]),
 ("economie", "Économie du Canada", [
  ("Quels sont les trois grands secteurs de l’économie canadienne?", "Services, fabrication et ressources naturelles", ["Tourisme, armée et politique", "Pêche, police et justice", "Banques, élections et culture"], "L’économie diversifiée repose largement sur les services, la fabrication et les ressources."),
  ("Quel pays est le principal partenaire commercial du Canada?", "Les États-Unis", ["Le Japon", "La France", "Le Brésil"], "La proximité et les accords commerciaux soutiennent d’importants échanges avec les États-Unis."),
  ("Quelle ressource a joué un rôle majeur dans les débuts économiques du Canada?", "La fourrure", ["Le pétrole seulement", "Le coton", "Le café"], "Le commerce des fourrures a façonné l’exploration et les relations historiques."),
  ("Dans quel secteur travaille la majorité des Canadiens?", "Le secteur des services", ["L’agriculture", "Les mines", "La pêche"], "Les services comprennent notamment les transports, l’éducation, la santé, la finance et le commerce."),
  ("Pourquoi le commerce international est-il important pour le Canada?", "Le Canada échange une grande quantité de biens, services et ressources avec le monde", ["Le Canada ne produit aucun bien", "Les provinces ne commercent pas entre elles", "Il remplace toutes les taxes"], "Le commerce soutient l’emploi et relie l’économie canadienne aux marchés mondiaux."),
  ("Quelle région est particulièrement connue pour le pétrole et le gaz?", "Les Prairies, notamment l’Alberta", ["L’Île-du-Prince-Édouard uniquement", "Le Nunavut uniquement", "La région de la capitale nationale"], "L’Alberta est un important producteur d’énergie; les Prairies sont aussi agricoles."),
 ]),
 ("regions", "Provinces, territoires et régions", [
  ("Combien le Canada compte-t-il de provinces et de territoires?", "10 provinces et 3 territoires", ["12 provinces et 1 territoire", "10 provinces et 2 territoires", "13 provinces"], "Le Canada est composé de dix provinces et de trois territoires."),
  ("Quelle est la capitale du Canada?", "Ottawa", ["Toronto", "Montréal", "Vancouver"], "Ottawa, en Ontario, est la capitale nationale."),
  ("Quelle est la capitale du Québec?", "Québec", ["Montréal", "Gatineau", "Sherbrooke"], "La ville de Québec est la capitale de la province; Montréal est sa plus grande ville."),
  ("Quelles provinces forment les provinces de l’Atlantique?", "Terre-Neuve-et-Labrador, Île-du-Prince-Édouard, Nouvelle-Écosse et Nouveau-Brunswick", ["Québec, Ontario, Manitoba et Saskatchewan", "Alberta, Saskatchewan, Manitoba et Ontario", "Yukon, Nunavut, T.N.-O. et Colombie-Britannique"], "Ces quatre provinces bordent l’Atlantique et possèdent une forte tradition maritime."),
  ("Quels sont les trois territoires?", "Yukon, Territoires du Nord-Ouest et Nunavut", ["Alberta, Yukon et Nunavut", "Labrador, Yukon et Nunavut", "Manitoba, Saskatchewan et Yukon"], "Les trois territoires occupent le Nord canadien."),
  ("Quelle province est la seule officiellement bilingue?", "Le Nouveau-Brunswick", ["Le Québec", "L’Ontario", "Le Manitoba"], "Le Nouveau-Brunswick est officiellement bilingue en français et en anglais."),
 ]),
]

questions=[]
templates=[
 "{q}",
 "Question de révision : {q}",
 "Pour réussir l’examen, peux-tu répondre : {q}",
 "Choisis la réponse exacte. {q}",
 "Selon le guide officiel, {q}",
]
counter=1
for order,(mid,title,facts) in enumerate(MODULES,1):
    for q,answer,distractors,explanation in facts:
        for variant,template in enumerate(templates,1):
            choices=[answer,*distractors]
            random.Random(f"{mid}-{counter}-{variant}").shuffle(choices)
            questions.append({"id":f"q{counter:03d}","module_id":mid,"module":title,"module_order":order,
              "question":template.format(q=q[0].lower()+q[1:] if variant==5 else q),"choices":choices,"answer":answer,
              "explanation":explanation,"source":SOURCE})
            counter+=1

out=Path(__file__).parent/"data"/"questions.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"{len(questions)} questions écrites dans {out}")
