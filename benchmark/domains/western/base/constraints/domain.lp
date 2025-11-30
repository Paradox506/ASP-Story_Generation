% Roles
role(carl, "You are carl. You have meds.").

% Define entities
character(carl).
place(gen_store).
object(meds).
attr(is_merchant(carl)).
attr(is_medicine(meds)).
attr(belongs_to(meds, carl)).

% possible actions
intentional_action(move(Dest)) :- place(Dest).
intentional_action(take(Obj, Ch)) :- object(Obj), character(Ch).
intentional_action(heal(Ch, Meds)) :- character(Ch), attr(is_medicine(Meds)).
intentional_action(kill(Ch)) :- character(Ch).
unintentional_action(snakebite).

% Intentions
intention(dead(X)) :- character(X).
intention(alive(X)) :- character(X).
intention(possessed_by(Obj, Subj)) :- character(Subj), object(Obj).

% 5x5 grid map with general store in the middle
place(l0_0).
connection(l0_0, l1_0).
connection(l0_0, l0_1).
place(l0_1).
connection(l0_1, l0_0).
connection(l0_1, l1_1).
connection(l0_1, l0_2).
place(l0_2).
connection(l0_2, l0_1).
connection(l0_2, l1_2).
connection(l0_2, l0_3).
place(l0_3).
connection(l0_3, l0_2).
connection(l0_3, l1_3).
connection(l0_3, l0_4).
place(l0_4).
connection(l0_4, l0_3).
connection(l0_4, l1_4).
place(l1_0).
connection(l1_0, l0_0).
connection(l1_0, l2_0).
connection(l1_0, l1_1).
place(l1_1).
connection(l1_1, l0_1).
connection(l1_1, l1_0).
connection(l1_1, l2_1).
connection(l1_1, l1_2).
place(l1_2).
connection(l1_2, l0_2).
connection(l1_2, l1_1).
connection(l1_2, gen_store).
connection(l1_2, l1_3).
place(l1_3).
connection(l1_3, l0_3).
connection(l1_3, l1_2).
connection(l1_3, l2_3).
connection(l1_3, l1_4).
place(l1_4).
connection(l1_4, l0_4).
connection(l1_4, l1_3).
connection(l1_4, l2_4).
place(l2_0).
connection(l2_0, l1_0).
connection(l2_0, l3_0).
connection(l2_0, l2_1).
place(l2_1).
connection(l2_1, l1_1).
connection(l2_1, l2_0).
connection(l2_1, l3_1).
connection(l2_1, gen_store).
place(gen_store).
connection(gen_store, l1_2).
connection(gen_store, l2_1).
connection(gen_store, l3_2).
connection(gen_store, l2_3).
place(l2_3).
connection(l2_3, l1_3).
connection(l2_3, gen_store).
connection(l2_3, l3_3).
connection(l2_3, l2_4).
place(l2_4).
connection(l2_4, l1_4).
connection(l2_4, l2_3).
connection(l2_4, l3_4).
place(l3_0).
connection(l3_0, l2_0).
connection(l3_0, l4_0).
connection(l3_0, l3_1).
place(l3_1).
connection(l3_1, l2_1).
connection(l3_1, l3_0).
connection(l3_1, l4_1).
connection(l3_1, l3_2).
place(l3_2).
connection(l3_2, gen_store).
connection(l3_2, l3_1).
connection(l3_2, l4_2).
connection(l3_2, l3_3).
place(l3_3).
connection(l3_3, l2_3).
connection(l3_3, l3_2).
connection(l3_3, l4_3).
connection(l3_3, l3_4).
place(l3_4).
connection(l3_4, l2_4).
connection(l3_4, l3_3).
connection(l3_4, l4_4).
place(l4_0).
connection(l4_0, l3_0).
connection(l4_0, l4_1).
place(l4_1).
connection(l4_1, l3_1).
connection(l4_1, l4_0).
connection(l4_1, l4_2).
place(l4_2).
connection(l4_2, l3_2).
connection(l4_2, l4_1).
connection(l4_2, l4_3).
place(l4_3).
connection(l4_3, l3_3).
connection(l4_3, l4_2).
connection(l4_3, l4_4).
place(l4_4).
connection(l4_4, l3_4).
connection(l4_4, l4_3).
connection(l3_4, l4_4).
connection(l4_3, l4_4).