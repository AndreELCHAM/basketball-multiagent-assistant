# LLM End-to-End Evaluation

**Overall Average Score:** 63.1%
**Total Keywords Hit:** 67.4% (62/92)
**Retrieval Hit Rate:** 88.9% (16/18)

|   ID | League   | Query                                            | Chunk Hit   | Score   | Answer Snippet                                                  |
|------|----------|--------------------------------------------------|-------------|---------|-----------------------------------------------------------------|
|    1 | FIBA     | In FIBA, what is the cylinder principle in ba... | ✅           | 100%    | ### Cylinder Principle in FIBA Basketball  The cylinder prin... |
|    2 | NBA      | How many timeouts are allowed per team in an ... | ✅           | 60%     | According to the NBA rulebook, each team is entitled to a sp... |
|    3 | FIBA     | Explain the dimensions and markings of a FIBA... | ✅           | 83%     | ### FIBA Basketball Court Dimensions and Markings  #### **Co... |
|    4 | FIBA     | What are the exact measurements of the basket... | ❌           | 50%     | The provided rulebook sources do not contain specific inform... |
|    5 | FIBA     | In FIBA free throw situations, where exactly ... | ✅           | 100%    | In FIBA free throw situations, the rebounding players must s... |
|    6 | FIBA     | In FIBA, what hand signals do basketball refe... | ERROR       | ERROR   | RetryError[<Future at 0x1f8135decf0 state=finished raised Ba    |
|    7 | FIBA     | Quelles sont les règles du marcher en basketb... | ✅           | 33%     | Les règles de déplacement (traveling) en basketball selon la... |
|    8 | NBA      | Combien de fautes personnelles un joueur peut... | ✅           | 20%     | Dans un match de la NBA, un joueur est disqualifié du jeu lo... |
|    9 | FIBA     | ¿Cuánto tiempo tiene un equipo para avanzar e... | ✅           | 40%     | Según las reglas de la FIBA, un equipo tiene 8 segundos para... |
|   10 |          | ¿Cuáles son las diferencias en la duración de... | ✅           | 0%      | Las diferencias en la duración de los períodos entre la NBA ... |
|   11 | FIBA_3x3 | yo so like what happens when someone gets a t... | ✅           | 60%     | In 3x3 basketball, when a player receives a technical foul, ... |
|   12 | NCAA     | In NCAA, wait can u explain the shot clock th... | ✅           | 100%    | Certainly! Here's a detailed explanation of the shot clock r... |
|   13 | NBA      | bruh what even counts as goaltending in the N... | ✅           | 67%     | To address your question about goaltending in the NBA, we ne... |
|   14 | FIBA_3x3 | how does the 12 second rule work in 3x3 hoops... | ✅           | 80%     | The 12-second rule in 3x3 basketball is designed to ensure t... |
|   15 | NBA      | ok so like in the nba can u challenge a foul ... | ✅           | 100%    | In the NBA, a head coach can challenge a foul call, but ther... |
|   16 | FIBA     | In FIBA, what constitutes a double dribble vi... | ✅           | 100%    | In FIBA, a double dribble violation is not explicitly define... |
|   17 | FIBA     | Define the backcourt violation rules under FI... | ✅           | 83%     | The backcourt violation rules under FIBA regulations are not... |
|   18 | FIBA_3x3 | How many players are on the court in a 3x3 ga... | ✅           | 60%     | In a 3x3 basketball game, each team has 3 players on the cou... |



## Detailed LLM Responses

### 1. In FIBA, what is the cylinder principle in basketball and how is it applied?
**Score:** 100% | **Chunk Hit:** ✅
**Keywords Hit:** cylinder, vertical, space, above, position / cylinder, vertical, space, above, position
**Full Answer:**
### Cylinder Principle in FIBA Basketball

The cylinder principle in FIBA basketball is a fundamental concept that defines the space a player occupies on the court. This principle is crucial for determining legal and illegal contact during the game. Here’s a detailed explanation based on the provided sources:

#### Definition and Application

1. **Cylinder Principle Overview**:
   - Each player has the right to occupy any position (cylinder) on the court not already occupied by an opponent. This principle protects the space on the court which the player occupies and the space above when jumping vertically within that space. (Source 2, Article 33.2)

2. **Visual Representation**:
   - **Diagram 6 Cylinder Principle** (Source 1 and Diagram for Source 1):
     - The diagram shows two players, one male and one female, each within an imaginary cylindrical space.
     - The male player is shown from the front with arms extended outward at shoulder height, palms facing forward, and legs apart with knees bent.
     - The female player is shown from the side with one arm extended outward and the other slightly bent, also with legs apart and knees bent.
     - Dashed lines outline the cylindrical space around each player, extending vertically above and below them.

3. **Verticality Principle**:
   - When a player leaves the vertical position (cylinder) and body contact occurs with an opponent who had already established that player’s own vertical position (cylinder), the player who left the vertical position (cylinder) is responsible for the contact. (Source 2, Article 33.2)
   - The defensive player must not be penalized for leaving the court vertically (within the cylinder) or having the hands and arms extended above and within that player’s own cylinder. (Source 2, Article 33.2)

4. **Legal Guarding Position**:
   - A defensive player has established an initial legal guarding position when:
     - Facing the opponent, and
     - Having both feet on the court. (Source 2, Article 33.3)
   - The legal guarding position extends vertically above (within the cylinder) from the court to the ceiling. The defensive player may raise the arms and hands above the head or jump vertically but must maintain them in a vertical position inside the imaginary cylinder. (Source 2, Article 33.3)

5. **Offensive Player Responsibilities**:
   - The offensive player, whether on the court or airborne, shall not cause contact with the defensive player in a legal guarding position by:
     - Using the arms to create more space (pushing off).
     - Spreading the legs or arms during or immediately after a shot for a goal. (Source 2, Article 33.2)

6. **Guarding a Player with the Ball**:
   - When guarding a player who controls (holding or dribbling) the ball, the elements of time and distance do not apply. The player with the ball must expect to be guarded and must be prepared to stop or change direction whenever an opponent takes an initial legal guarding position in front of that offensive player, even if this is done within a fraction of a second. (Source 2, Article 33.4)

### Summary

The cylinder principle in FIBA basketball ensures that each player has a defined space on the court that they can occupy without interference. This principle is visually represented by the cylindrical space around each player, as shown in Diagram 6. The verticality principle and the concept of a legal guarding position are key components that help determine the legality of contact during the game. The offensive player must respect the defensive player's cylinder and avoid causing contact, while the defensive player must maintain a vertical position within their own cylinder to avoid being penalized.

---

### 2. How many timeouts are allowed per team in an NBA game and when can they be called?
**Score:** 60% | **Chunk Hit:** ✅
**Keywords Hit:** timeout, team, mandatory / timeout, team, regular, mandatory, quarter
**Full Answer:**
According to the NBA rulebook, each team is entitled to a specific number of timeouts during a game, and there are specific rules regarding when these timeouts can be called. Here are the relevant details:

1. **Number of Timeouts:**
   - Each team is entitled to **seven (7) charged timeouts** during regulation play. (Source 4, Section VI(a))
   - In overtime periods, each team is allowed **two (2) team timeouts**. (Source 2, Section VIII(b))

2. **Timeouts in the Fourth Period:**
   - Each team is limited to **no more than four (4) timeouts** in the fourth period. (Source 4, Section VI(a))
   - After the later of (i) the three-minute mark of the fourth period or (ii) the conclusion of the second mandatory timeout of the fourth period, each team is limited to **two (2) team timeouts**. (Source 4, Section VI(a))

3. **Mandatory Timeouts:**
   - There must be **two mandatory timeouts** in each period. If neither team has taken a timeout prior to 6:59 of the period, it is mandatory for the Official Scorer to take it at the first dead ball and charge it to the home team (or the second team named in the official schedule for a neutral site game). If no subsequent timeouts are taken prior to 2:59, another mandatory timeout is taken and charged to the team not previously charged. (Source 2, Section VIII(c))

4. **When Timeouts Can Be Called:**
   - A request for a timeout by a player in the game or the head coach shall be granted only when the ball is dead or in control of a player on the team making the request. A request at any other time shall be ignored. (Source 2, Section VIII(d))
   - In the last two minutes of the fourth period and last two minutes of any overtime period, if a timeout is charged to the offensive team and the ball is out-of-bounds in the backcourt, or after securing the ball from a rebound or a change of possession in the backcourt, the team granted the timeout shall have the option of putting the ball into play at the 28’ hash mark in the frontcourt or at the designated spot out-of-bounds. (Source 2, Section VIII(g))

5. **Excess Timeouts:**
   - Requests for a timeout in excess of those available to the team at that point in the game shall be granted, and a technical foul shall be assessed. (Source 1, Section VII(k))

These rules provide a comprehensive framework for the number and timing of timeouts in an NBA game.

---

### 3. Explain the dimensions and markings of a FIBA basketball court including the three-point line distance
**Score:** 83% | **Chunk Hit:** ✅
**Keywords Hit:** court, dimensions, three-point, line, 6.75 / court, dimensions, three-point, line, metre, 6.75
**Full Answer:**
### FIBA Basketball Court Dimensions and Markings

#### **Court Dimensions**
- **Main Playing Court**: 28 meters in length by 15 meters in width, measured from the inner edge of the boundary lines.
- **Overall Floor Area**: 32 meters in length by 19 meters in width, including a further boundary lane of at least 2 meters wide around the main court.

#### **Court Markings**
- **Central Circle**: Located at the midpoint of the court, with a radius of 1.80 meters measured to the outer edge of the circumference.
- **Sidelines and Endlines**: Solid lines, 5 cm in width, forming the outer boundaries of the court.
- **Centre Line**: Divides the court into two equal halves, running parallel to the endlines and extending 0.15 meters beyond each sideline.
- **Three-Point Arc**: An arc with a radius of 6.75 meters measured from the point on the court beneath the exact center of the opponents' basket to the outer edge of the arc. The arc is joined to two parallel lines extending from and perpendicular to the endline, with the outer edge 0.90 meters from the inner edge of the sidelines.
- **Free-Throw Line**: Parallel to each endline, with its furthest edge 5.80 meters from the inner edge of the endline and 3.60 meters long. Its mid-point lies on the imaginary line joining the mid-point of the two endlines.
- **Restricted Area**: A rectangular area marked on the court, limited by the endlines, the extended free-throw lines, and lines originating at the endlines. The outer edges of these lines are 2.45 meters from the mid-point of the endlines and terminate at the outer edge of the extended free-throw lines.
- **No-charge Semi-circle Area**: A semi-circular area with a radius of 1.30 meters measured from the point on the court beneath the exact center of the basket to the outer edge of the semi-circle. The semi-circle line is joined to two parallel lines perpendicular to the endline, with the outer edge 1.30 meters from the point on the court beneath the exact center of the basket, 0.375 meters in length, and ending 1.20 meters from the inner edge of the endline.
- **Throw-in Lines**: Four throw-in lines, two on each sideline, 0.15 meters in length, marked outside the court with the outer edge 8.325 meters from the inner edge of the nearest endline.
- **Team Bench Areas**: Marked outside the court, limited by two lines, with 16 seats available for the head coach, substitutes, excluded players, and accompanying delegation members. Any other persons must be located at least 2 meters behind the team bench.

#### **Three-Point Line Distance**
- The three-point line is an arc with a radius of 6.75 meters measured from the point on the court beneath the exact center of the opponents' basket to the outer edge of the arc. The distance from the center of the basket to the baseline of the restricted area is 1.575 meters.

### Diagram References
- **Diagram 1 Full size court**: Provides a comprehensive overview of the court layout, including all essential markings, dimensions, and key areas.
- **Diagram 2 Court and floor**: Focuses on the geometric layout and dimensions of the basketball court, including the further boundary lane.
- **Diagram 3 Restricted area**: Illustrates the restricted area and no-charge semi-circle area near the basket.
- **Diagram 4 2-point/3-point goal area**: Simplified diagram showing the 2-point and 3-point goal areas.
- **Diagram 5 Scorer's table and substitution chairs**: Layout of the scorer's table and team bench areas.

These diagrams and descriptions provide a detailed and accurate representation of the FIBA basketball court, including the three-point line distance.

---

### 4. What are the exact measurements of the basketball ring and its mounting plate according to FIBA rules?
**Score:** 50% | **Chunk Hit:** ❌
**Keywords Hit:** ring, mounting, plate / ring, diameter, mounting, plate, backboard, 450mm
**Full Answer:**
The provided rulebook sources do not contain specific information about the exact measurements of the basketball ring and its mounting plate. The sources focus on court dimensions, markings, and other areas of the court, but they do not provide detailed specifications for the basketball ring and its mounting plate.

To answer your question accurately, you would need to refer to a different section of the FIBA rulebook or another official document that specifically addresses the dimensions and specifications of the basketball ring and its mounting plate.

---

### 5. In FIBA free throw situations, where exactly do the rebounding players stand along the lane?
**Score:** 100% | **Chunk Hit:** ✅
**Keywords Hit:** free throw, lane, rebound, position, player, space / free throw, lane, rebound, position, player, space
**Full Answer:**
In FIBA free throw situations, the rebounding players must stand in specific positions along the lane. According to the provided sources, the following rules and diagrams outline the positioning:

1. **Player Positions**:
   - **44.2.4** states: "The players in the free-throw rebound places shall be entitled to occupy alternating positions in these spaces, of 1 m in depth (Diagram 7)."
   - During the free throws, these players must not:
     - Occupy free-throw rebound places to which they are not entitled.
     - Enter the restricted area, the neutral zone, or leave the free-throw rebound place until the ball has left the hand(s) of the free-throw shooter.
     - Distract the free-throw shooter by their actions.

2. **Diagram 7** (Players' positions during free throws):
   - **Player Positions**:
     - On the left side of the lane:
       - B3 is at the top of the lane near the free-throw line.
       - A1 is below B3, closer to the baseline.
       - B1 is at the bottom of the lane near the baseline.
     - On the right side of the lane:
       - A2 is at the top of the lane near the free-throw line.
       - B2 is below A2, closer to the baseline.
     - At the top of the lane, outside the three-point line:
       - A4 is on the left side.
       - B5 is on the right side.
       - A3 is positioned at the center of the lane, near the free-throw line.

3. **Free-Throw Rebound Places**:
   - The free-throw rebound places are marked as alternating spaces along the lane, each 1 meter in depth. These spaces are designed to ensure that players from both teams are positioned in an alternating manner, as shown in Diagram 7.

4. **Neutral Zone**:
   - The neutral zone is the area directly behind the free-throw line and in front of the free-throw shooter. Players are not allowed to enter this zone until the ball has left the shooter's hands.

In summary, the rebounding players must stand in alternating positions along the lane, each in a 1-meter deep space, as illustrated in Diagram 7. They must not enter the restricted area, the neutral zone, or leave their designated positions until the ball has been released by the free-throw shooter.

---

### 6. In FIBA, what hand signals do basketball referees use to indicate different types of fouls?
**Error:** RetryError[<Future at 0x1f8135decf0 state=finished raised BadRequestError>]

---

### 7. Quelles sont les règles du marcher en basketball selon la FIBA?
**Score:** 33% | **Chunk Hit:** ✅
**Keywords Hit:** travel, dribble / travel, pivot, foot, step, move, dribble
**Full Answer:**
Les règles de déplacement (traveling) en basketball selon la FIBA sont détaillées dans le règlement officiel. Voici les points clés :

1. **Définition du déplacement (traveling)** :
   - Un joueur ne peut pas prendre plus de deux pas sans dribbler la balle après avoir arrêté son dribble ou après avoir attrapé la balle (Article 15.1.3).
   - Le déplacement commence lorsque le joueur a rassemblé la balle et qu'elle repose dans sa main(s), après avoir terminé un dribble ou avoir attrapé la balle en l'air, et continue le mouvement de tir avant de lâcher la balle (Article 15.1.3).

2. **Mouvement continu lors des drives vers le panier** :
   - Le mouvement continu lors des drives vers le panier est une action où le joueur rassemble la balle après avoir terminé un dribble ou l'avoir attrapée en l'air, puis continue le mouvement de tir vers le panier, généralement vers le haut (Article 15.1.3).
   - Ce mouvement se termine lorsque la balle a quitté la main(s) du joueur ou, si le joueur est en l'air, lorsque ses deux pieds ont touché le sol (Article 15.1.3).

3. **Acte de tir** :
   - Pour qu'un joueur soit considéré comme étant en acte de tir, il doit être dans le frontcourt (Article 15.1.4).
   - Il n'y a pas de relation entre le nombre de pas légaux pris et l'acte de tir (Article 15.1.5).

4. **Exceptions** :
   - Un joueur peut être n'importe où sur le terrain lors de la dernière action avant :
     - L'expiration du chronomètre de jeu pour la fin du quart-temps ou du temps supplémentaire.
     - L'expiration du chronomètre de tir à tout moment du jeu (Article 15.1.4).

5. **Perturbation par un adversaire** :
   - Si un joueur est en acte de tir et que son bras est retenu par un adversaire, empêchant ainsi le tir, il n'est pas nécessaire que la balle quitte la main(s) du joueur (Article 15.1.6).

6. **Perte de l'acte de tir** :
   - Si un joueur est en acte de tir lors d'un tir en saut ou d'un autre tir en mouvement et est fauté, il perd son statut d'acte de tir s'il :
     - Passe la balle.
     - Déplace la balle vers le haut dans une direction éloignée du panier.
     - N'est pas face au panier lorsqu'il déplace la balle vers le haut (Article 15.1.7).
   - Si un joueur est en acte de tir lors d'un drive vers le panier et passe la balle après avoir été fauté, il perd son statut d'acte de tir (Article 15.1.8).

Ces règles sont essentielles pour comprendre les conditions sous lesquelles un joueur peut être considéré comme en déplacement illégal (traveling) en basketball selon la FIBA.

---

### 8. Combien de fautes personnelles un joueur peut-il commettre avant d'être exclu dans un match NBA?
**Score:** 20% | **Chunk Hit:** ✅
**Keywords Hit:** six / personal, foul, disqualified, six, player
**Full Answer:**
Dans un match de la NBA, un joueur est disqualifié du jeu lorsqu'il commet son sixième faute personnelle. Cette règle est clairement énoncée dans le **Règlement n° 3, Section I(a)** du rulebook de la NBA.

Voici la citation exacte :
"Un joueur est disqualifié du jeu lorsqu'il reçoit son sixième faute personnelle."

Donc, la réponse à votre question est que **un joueur peut commettre cinq fautes personnelles avant d'être disqualifié**. La sixième faute personnelle entraîne automatiquement sa disqualification.

---

### 9. ¿Cuánto tiempo tiene un equipo para avanzar el balón a la mitad ofensiva según las reglas de la FIBA?
**Score:** 40% | **Chunk Hit:** ✅
**Keywords Hit:** backcourt, frontcourt / eight, seconds, backcourt, frontcourt, advance
**Full Answer:**
Según las reglas de la FIBA, un equipo tiene 8 segundos para avanzar el balón a su campo de ataque (frontcourt) después de que un jugador en el campo defensivo (backcourt) adquiere el control de un balón en juego, o cuando el balón toca o es legalmente tocado por cualquier jugador en el backcourt durante un saque de banda y el equipo que realiza el saque de banda mantiene el control del balón en su backcourt. Esto se especifica en el **Artículo 28** del reglamento de la FIBA.

**Artículo 28 8 segundos**
- **28.1.1** Cualquiera de las siguientes situaciones:
  - Un jugador en el backcourt adquiere el control de un balón en juego.
  - Durante un saque de banda, el balón toca o es legalmente tocado por cualquier jugador en el backcourt y el equipo que realiza el saque de banda mantiene el control del balón en su backcourt.
- **28.1.2** El equipo ha causado que el balón ingrese a su frontcourt cuando:
  - El balón, sin estar en control de ningún jugador, toca el frontcourt.
  - El balón toca o es legalmente tocado por un jugador ofensivo que tiene ambos pies completamente en contacto con el frontcourt.
  - El balón toca o es legalmente tocado por un jugador defensivo que tiene parte del cuerpo en contacto con el backcourt.
  - El balón toca a un árbitro que tiene parte del cuerpo en contacto con el frontcourt del equipo en control del balón.
  - Durante un dribling desde el backcourt al frontcourt, el balón y ambos pies del dribler están completamente en contacto con el frontcourt.

Por lo tanto, la respuesta a tu pregunta es que un equipo tiene **8 segundos** para avanzar el balón a su campo de ataque según las reglas de la FIBA.

---

### 10. ¿Cuáles son las diferencias en la duración de los períodos entre la NBA y la NCAA?
**Score:** 0% | **Chunk Hit:** ✅
**Keywords Hit:** None / quarter, half, minutes, period, time
**Full Answer:**
Las diferencias en la duración de los períodos entre la NBA y la NCAA son las siguientes:

- **NBA**: Cada período dura 12 minutos. Hay cuatro períodos en total.
- **NCAA**: Cada período dura 20 minutos. Hay dos períodos en total.

Esta información se puede encontrar en las reglas oficiales de cada liga, aunque los documentos proporcionados no especifican directamente la duración de los períodos. Sin embargo, esta es la información correcta según las reglas conocidas de ambas ligas.

---

### 11. yo so like what happens when someone gets a tech foul in 3x3 basketball? is it different from regular ball?
**Score:** 60% | **Chunk Hit:** ✅
**Keywords Hit:** technical, foul, free throw / technical, foul, free throw, penalty, unsportsmanlike
**Full Answer:**
In 3x3 basketball, when a player receives a technical foul, the following procedures are followed according to the FIBA 3x3 rules:

1. **Free Throw Awarded:**
   - The opponents of the player who committed the technical foul are awarded 1 free throw. (Source 4, Art. 36.3.1)

2. **Game Resumption:**
   - After the free throw is administered, the game is resumed with a check-ball. The check-ball is administered by the team that had control of the ball or was entitled to the ball when the technical foul was called. (Source 4, Art. 36.3.1)

3. **Team Foul Count:**
   - The technical foul counts as a team foul. (Source 4, Art. 36.3.1)

4. **Immediate Administration:**
   - The free throw for the technical foul is administered immediately, regardless of whether the order of any other possible penalties for any other fouls has been determined or whether the administration of the penalties has been started. (Source 1)

5. **Check-Ball Situations:**
   - If a valid field goal or the last free throw is scored at the same time as the technical foul, the game is resumed with a check-ball for the last defensive team. (Source 1)

6. **Jump Ball Situations:**
   - If neither team had control of the ball nor was entitled to the ball when the technical foul was called, a jump ball situation occurs. The game is resumed with a check-ball for the last defensive team. (Source 1)

These rules are specific to 3x3 basketball and may differ from the rules in 5-on-5 basketball.

---

### 12. In NCAA, wait can u explain the shot clock thing in college bball? like when does it reset n stuff
**Score:** 100% | **Chunk Hit:** ✅
**Keywords Hit:** shot clock, seconds, reset, possession, offensive / shot clock, seconds, reset, possession, offensive
**Full Answer:**
Certainly! Here's a detailed explanation of the shot clock rules in NCAA college basketball, based on the provided rulebook sources:

### Starting the Shot Clock
The shot clock is started in the following situations (Rule 5, Section 10, Art. 3):
- **a.** When an inbounds player legally touches the ball after the throw-in has been released.
- **b.** When a team gains initial control following a jump ball or an unsuccessful try for a goal.
- **c.** When there is a change of team control.
- **d.** When tenths of a second are displayed with less than five seconds on the shot clock, and the ball is legally touched inbounds and an official immediately signals to stop the clock, a minimum of 3/10ths (0.3) of a second must expire on the shot clock.

### Stopping the Shot Clock
The shot clock is stopped in the following situations (Rule 5, Section 11, Art. 1 and Art. 2):
- **a.** When an official signals a foul.
- **b.** When an official signals a held ball.
- **c.** When an official signals a violation.
- **d.** At the expiration of time for each period.
- **e.** Because of an injury, blood situation, or a lost, displaced, or irritated contact lens.
- **f.** To confer with the scorers, timers, or shot-clock operator.
- **g.** Because of unusual delay in a dead ball being made live.
- **h.** For any emergency.

### Resetting the Shot Clock
The shot clock is reset in the following situations (Rule 2, Section 9, Art. 5):
- **a.** Reset to 30 seconds when:
  - 1. There is a change in team control and the ball remains live or after a score by the opponent.
  - 2. Team control is re-established in the backcourt after the team loses control of the ball.
  - 3. A held ball occurs or any other situation occurs where the alternating-possession arrow must be used to determine team possession and the alternating possession arrow favors the defense for a throw-in in the backcourt.
  - 4. A try for goal, pass (other than a throw-in), or deflection strikes the ring or flange and control is gained by the non-shooting team.
  - 5. A single personal or technical foul is assessed to the defensive team while the ball is in control of the offensive team in the backcourt.
  - 6. A double personal foul when only one of the fouls is flagrant and it is assessed against the offense in their front court and the defense is awarded the ball for a throw-in in their backcourt. If the flagrant foul is assessed against the defense, the shot clock shall be reset to 20 seconds or time remaining (whichever is greater) per Rule 2-11-6c1.
  - 7. A violation occurs, except as in Rules 2-11-6a1 and 2, and the defense is awarded the ball for a throw-in in the backcourt. If the throw-in is in the front court, the shot clock shall be reset to 20 seconds per Rule 2-11-6d6.
  - 8. An inadvertent whistle occurs when there was no player or team control at the time of the whistle and the alternating-possession arrow favors either team for a throw-in in the backcourt.
  - 9. During a jump ball, one team causes the ball to be out of bounds and the other team is awarded the ball for a throw-in in the backcourt.
- **b.** Reset to 20 seconds or the time remaining (whichever is greater) when:
  - 1. A personal or technical foul is assessed to the defensive team and the ball is to be inbounded in the front court.

### Shot Clock Violation
A shot clock violation occurs when:
- A try for a field goal does not leave the shooter’s hand before the expiration of the allotted shot-clock time (as indicated by the sounding of the shot-clock horn).
- The try does leave the shooter’s hand before the expiration of the allotted shot-clock time, but it does not subsequently strike the ring or flange or enter the basket (Rule 9, Section 11, Art. 4).

### Summary
- The shot clock starts when the ball is legally touched after a throw-in, when a team gains control after a jump ball, or when there is a change of team control.
- The shot clock stops when an official signals a foul, held ball, or violation, or for other specific game stoppages.
- The shot clock resets to 30 seconds in various scenarios, such as a change in team control, a held ball, or a foul by the defensive team.
- The shot clock resets to 20 seconds or the time remaining (whichever is greater) when a personal or technical foul is assessed to the defensive team and the ball is to be inbounded in the front court.
- A shot clock violation occurs if the ball does not leave the shooter’s hand before the shot clock expires or if it does leave the shooter’s hand but does not hit the ring or enter the basket.

This should provide a comprehensive understanding of the shot clock rules in NCAA college basketball.

---

### 13. bruh what even counts as goaltending in the NBA?? my friend says it's different from college
**Score:** 67% | **Chunk Hit:** ✅
**Keywords Hit:** goaltending, basket, interference, ball / goaltending, basket, interference, ball, descending, cylinder
**Full Answer:**
To address your question about goaltending in the NBA, we need to look at the specific rules related to basket interference and goaltending. The provided sources do not explicitly define goaltending, but they do provide relevant information about basket interference and related violations.

### Basket Interference and Goaltending

#### **RULE NO. 6—PUTTING BALL IN PLAY—LIVE/DEAD BALL**
- **Section I—Start of Games/Periods and Others**
  - **e.** On the following infractions, the ball shall be awarded to the opposing team out-of-bounds on the nearest sideline at the free throw line extended:
    - (3) Illegal assist in scoring
    - (10) Offensive basket interference
  - **f.** On the following infractions, the ball shall be awarded to the opposing team on the baseline at the nearest spot outside the three-second area extended:
    - (3) Defensive goaltending (all privileges remain)

#### **RULE NO. 5—SCORING AND TIMING**
- **Section I—Scoring**
  - **a.** A legal field goal or free throw attempt shall be scored when a ball from the playing area enters the basket from above and remains in or passes through the net.
  - **d.** A field goal accidentally scored in an opponent’s basket shall be added to the opponent’s score, credited to the opposing player nearest the player whose actions caused the ball to enter the basket.
  - **e.** It is a violation for a player to attempt a field goal at an opponent’s basket. The opposing team will be awarded the ball at the free throw line extended.

### Definition of Goaltending

While the provided sources do not explicitly define goaltending, we can infer the definition from the context of basket interference and related violations. Goaltending in the NBA is a specific type of basket interference that occurs when a player interferes with the ball while it is on its downward flight towards the basket, on the rim, or directly above the basket.

### Key Points:
1. **Downward Flight**: A player cannot touch the ball while it is on its downward flight towards the basket after it has touched the backboard or the rim.
2. **On the Rim**: A player cannot touch the ball while it is on the rim.
3. **Directly Above the Basket**: A player cannot touch the ball while it is directly above the basket and has the possibility of entering the basket.

### Penalties:
- **Offensive Goaltending**: If an offensive player commits goaltending, the basket does not count, and the ball is awarded to the opposing team.
- **Defensive Goaltending**: If a defensive player commits goaltending, the basket counts, and the ball is awarded to the offensive team.

### Comparison to College (NCAA)
In the NCAA, the rules for goaltending are similar, but there are some differences:
- **NCAA Rules**: In the NCAA, a player cannot touch the ball while it is on its way up towards the basket if it has the possibility of entering the basket. This is a stricter rule compared to the NBA, where the ball must be on its downward flight or on the rim.

### Conclusion
In the NBA, goaltending is a violation that occurs when a player interferes with the ball while it is on its downward flight towards the basket, on the rim, or directly above the basket. The penalty for goaltending depends on whether the violation is committed by an offensive or defensive player. The rules in the NBA are slightly different from those in the NCAA, particularly in the timing of when a player can touch the ball.

For a more detailed and official definition, you may want to refer to the official NBA rulebook, which provides comprehensive rules and diagrams.

---

### 14. how does the 12 second rule work in 3x3 hoops lol never understood it
**Score:** 80% | **Chunk Hit:** ✅
**Keywords Hit:** 12, seconds, shot clock, 3x3 / 12, seconds, shot clock, possession, 3x3
**Full Answer:**
The 12-second rule in 3x3 basketball is designed to ensure that teams actively attempt to score and do not stall the game. Here’s a detailed breakdown of how it works, based on **Art. 29 12 seconds** from the FIBA 3x3 rulebook:

### Key Points of the 12-Second Rule

1. **When the 12-Second Clock Starts:**
   - **29.1.1** The 12-second clock starts when:
     - A player gains control of a live ball on the playing court.
     - On a check-ball, the ball is in the hands of the offensive player after the check-ball has been completed.
     - Following each successful field goal or last free throw, the ball is in the hands of the player from the non-scoring team.

2. **What Constitutes a Valid Shot:**
   - **29.1.2** To avoid a violation, the ball must:
     - Leave the player's hand(s) before the shot clock signal sounds.
     - After leaving the player's hand(s), the ball must touch the ring or enter the basket.

3. **Handling the Shot Clock Signal:**
   - **29.1.3** If a shot is attempted near the end of the 12-second period and the shot clock signal sounds while the ball is in the air:
     - If the ball enters the basket, no violation has occurred, the signal is disregarded, and the goal counts.
     - If the ball touches the ring but does not enter the basket, no violation has occurred, the signal is disregarded, and the game continues.
     - If the ball misses the ring, a violation has occurred. However, if the opponents gain immediate and clear control of the ball, the signal is disregarded, and the game continues.

4. **Referee Intervention:**
   - **29.2.1** If the court is not equipped with a shot clock and a team is not sufficiently trying to attack the basket, the referees shall give the offensive team information on the remaining seconds by counting them loudly and signaling with an extended arm in the last 5 seconds.

5. **Resetting the Shot Clock:**
   - The shot clock is reset whenever the game is stopped by a referee for a foul or violation (not for the ball going out-of-bounds) by the team not in control of the ball.

### Summary
The 12-second rule in 3x3 basketball ensures that teams must attempt a shot within 12 seconds of gaining control of the ball. The shot must leave the player's hand before the 12 seconds are up and must either touch the ring or enter the basket to avoid a violation. Referees can also intervene if there is no shot clock to ensure the game remains active and competitive.

---

### 15. ok so like in the nba can u challenge a foul call? how does that work exactly
**Score:** 100% | **Chunk Hit:** ✅
**Keywords Hit:** challenge, coach, review, overturn, timeout / challenge, coach, review, overturn, timeout
**Full Answer:**
In the NBA, a head coach can challenge a foul call, but there are specific rules and procedures that must be followed. Here's how it works:

### Overview of Coach's Challenge
- **Each team is entitled to one Challenge per game.** If a team's first Challenge is successful, the team will be awarded a second Challenge. (Source 2, Section I(b))

### Challengeable Events
- A team may use a Challenge to trigger instant replay review of the following events:
  1. **A called personal foul charged to its own team.**
  2. **A called out-of-bounds violation where its own team was not awarded possession.**
  3. **A called goaltending or basket interference violation.** (However, in the last two minutes of the fourth period and last two minutes of any overtime, a team cannot use a Challenge to review a called goaltending or basket interference violation; these reviews are exclusively triggered by the on-court game officials.) (Source 2, Section I(c))

### Procedure to Initiate the Challenge
1. **Call a legal timeout immediately after the call in question.** (Source 2, Section II(a)(1))
2. **Simultaneously signal for a Challenge** by utilizing the instant replay signal (i.e., twirling an index finger) toward the game official(s) during the same interaction with the game official(s) in which the timeout was called. (Source 2, Section II(a)(2))
3. **Notify the game official(s) of the specific event that the team is challenging.** (Source 2, Section II(a)(3))

### Time Constraints
- The window to challenge the final ruling on the play ends when the ball is given to the inbounder or free throw shooter, a jump ball is tossed, or 30 seconds after the team has been notified of the final ruling on the play (whichever is applicable). (Source 1, Section III(c))

### Reviewable Matters
- If an instant replay review of a called foul is triggered by a Challenge, the on-court crew chief will review the video to evaluate whether the foul was correctly called. The crew chief may also review other specific matters, including:
  - Whether the correct player was called for the foul.
  - Whether a different foul proximate to the called foul should have been called.
  - Aspects related to continuation, such as whether the foul occurred before the offensive player began their shooting motion.
  - Whether a goaltending or basket interference violation occurred.
  - Whether the game clock or shot clock expired before the foul.
  - Whether a boundary line violation occurred.
  - Whether an 8-second backcourt violation occurred.
  - Whether any unsportsmanlike acts or unnecessary contact occurred.
  - Whether a flopping violation proximate to the called foul should be assessed or rescinded. (Source 1, Section III(a))

### Consequences of a Challenge
- If the Challenge is successful, the original call is overturned, and the game is reset to the appropriate state. If the Challenge is unsuccessful, the team loses one timeout. (Source 1, Section III(e))

### Non-Challengeable Events
- A team cannot challenge a called personal foul charged to the opposing team, continuation issues, technical fouls, flagrant fouls, or violations such as traveling, carrying, double dribble, flopping, or offensive or defensive three-seconds. (Source 2, Section I(d))

By following these procedures and constraints, a head coach can challenge a foul call in the NBA.

---

### 16. In FIBA, what constitutes a double dribble violation and what is the penalty?
**Score:** 100% | **Chunk Hit:** ✅
**Keywords Hit:** dribble, double, violation, hand, ball, control / dribble, double, violation, hand, ball, control
**Full Answer:**
In FIBA, a double dribble violation is not explicitly defined in the provided sources. However, based on the general rules of basketball and the context of the provided sources, a double dribble violation typically occurs when a player gains control of the ball, dribbles it, gains control again with both hands or by allowing the ball to come to rest in one or both hands, and then dribbles it again. This is considered a violation of the rules.

### Double Dribble Violation
- **Definition**: According to the general principles of basketball, a double dribble occurs when a player:
  - Dribbles the ball, gains control of it with both hands or allows it to come to rest in one or both hands, and then dribbles it again.
  - Dribbles the ball, loses control of it, regains control, and then dribbles it again without the ball being touched by another player.

### Penalty
- **Penalty**: The penalty for a double dribble violation is:
  - The ball is awarded to the opponents for a throw-in from the place nearest to the infraction, except from directly behind the backboard, unless otherwise stated in these rules. (Source: **Article 22.2 Penalty** from **RULE FIVE – VIOLATIONS**)

### Relevant Rule
- **Article 24 Dribbling** from **RULE FIVE – VIOLATIONS**:
  - **24.1.1** A dribble is the movement of a live ball caused by a player in control of that ball who throws, taps, rolls, or bounces the ball on the court.
  - **24.1.2** A dribble starts when a player, having gained control of a live ball on the court, throws, taps, rolls, or bounces it on the court and touches it again before it touches another player.
  - **24.1.3** During a dribble, the player may not place any part of the hand under the ball and carry it from one point to another or bring the ball to a pause and then continue to dribble. During a dribble, the ball may be thrown into the air provided the ball touches the court or another player before the player who threw it touches it again with the hand.

While the specific term "double dribble" is not explicitly mentioned in the provided sources, the rules regarding dribbling and violations cover the concept and the penalty for such an infraction.

---

### 17. Define the backcourt violation rules under FIBA regulations
**Score:** 83% | **Chunk Hit:** ✅
**Keywords Hit:** backcourt, violation, frontcourt, line, return / backcourt, violation, frontcourt, centre, line, return
**Full Answer:**
The backcourt violation rules under FIBA regulations are not explicitly detailed in the provided sources. However, based on the information available, we can infer some relevant details from the definitions and court markings.

### Backcourt Violation Rules (Inferred from FIBA Rules)

1. **Definition of Backcourt and Frontcourt:**
   - **Backcourt:** A team's backcourt consists of its team's own basket, the inbounds part of the backboard, and that part of the court limited by the endline behind its own basket, the sidelines, and the center line. (Article 2.3, Source 1)
   - **Frontcourt:** A team's frontcourt consists of the opponents' basket, the inbounds part of the backboard, and that part of the court limited by the endline behind the opponents' basket, the sidelines, and the inner edge of the center line nearest to the opponents' basket. (Article 2.4, Source 1)

2. **General Violation Rule:**
   - A violation is an infraction of the rules. (Article 22.1, Source 3)
   - The penalty for a violation is that the ball shall be awarded to the opponents for a throw-in from the place nearest to the infraction, except from directly behind the backboard, unless otherwise stated in these rules. (Article 22.2, Source 3)

3. **Specific Backcourt Violation:**
   - While not explicitly stated in the provided sources, a backcourt violation typically occurs when a player with the ball, after having established a frontcourt position, returns to the backcourt with the ball. This is a common rule in basketball and is likely to be similar in FIBA regulations.

### Inferred Backcourt Violation Rule:
- **Backcourt Violation:** A player who has established a frontcourt position with the ball (i.e., the ball is in the frontcourt) cannot return to the backcourt with the ball. If a player does return to the backcourt with the ball, it is a backcourt violation, and the ball is awarded to the opposing team for a throw-in from the place nearest to the infraction.

### Note:
- The specific rule for backcourt violations is not directly provided in the given sources. For a precise and authoritative rule, you would need to refer to the full FIBA rulebook, particularly the section on violations or the specific rule that addresses backcourt violations.

If you need the exact rule, I recommend consulting the complete FIBA rulebook or the official FIBA website for the most accurate and detailed information.

---

### 18. How many players are on the court in a 3x3 game and what are the substitution rules?
**Score:** 60% | **Chunk Hit:** ✅
**Keywords Hit:** player, team, substitution / player, team, substitution, three, roster
**Full Answer:**
In a 3x3 basketball game, each team has 3 players on the court. According to **Art. 1.1** of the FIBA 3x3 rules, the game is played by 2 teams of 3 players each, with a maximum of one substitute per team.

Regarding substitution rules, the provided sources do not explicitly detail the substitution procedures. However, it is generally understood that substitutions in 3x3 basketball can be made during dead ball situations, such as timeouts or after a successful free throw. For a more detailed and precise set of substitution rules, you would need to refer to the specific section of the FIBA 3x3 rulebook that covers substitutions, which is not provided in the current sources.

---
