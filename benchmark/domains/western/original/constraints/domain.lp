% Roles
role(hank, "You are hank. You are timmy's parent. You are armed.").
role(timmy, "You are timmy. You are hank's child.").
role(william, "You are william. You are sheriff.").
role(carl, "You ara carl. You can meds.").

% Define entities
character(hank;timmy;william;carl).
place(ranch;saloon;gen_store).
object(meds).

% Entity attributes
attr(is_medicine(meds)).
attr(is_sheriff(william)).
attr(is_parent_of(hank, timmy)).
attr(is_armed(hank)).
attr(is_armed(william)).
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