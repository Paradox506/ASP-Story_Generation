% Roles
role(alice, "You are Aladdin. You are loyal to the king Mamoud.").
role(kamy, "You are Mamoud.").
role(polly, "You are Jasmine.").
role(david, "You are dragon").
role(galileo, "You are genie").

% Define entities
character(alice;kamy;polly;david;galileo).
place(castle;mountain).
object(lamp).

% Entity attributes
attr(is_scary(david)).
attr(is_scary(galileo)).
attr(is_knight(alice)).

attr(is_servant(Ch)) :- attr(is_loyal_to(Ch, _)).

% possible actions
intentional_action(move(Dest)) :- place(Dest).
intentional_action(kill(Victim)) :- character(Victim).
intentional_action(marry(Ch)) :- character(Ch).
intentional_action(cast_love_spell(Target, Lover)) :- character(Target), character(Lover).
intentional_action(pillage(Body, Obj)) :- character(Body), object(Obj).
intentional_action(give(Givee, Obj)) :- character(Givee), object(Obj).
delegation_action(order_to_kill(Knight, Victim)) :- attr(is_servant(Knight)), character(Victim).
delegation_action(order_to_obtain(Knight, Obj)) :- attr(is_servant(Knight)), object(Obj).
intentional_action(Act)  :- delegation_action(Act).
non_delegation_action(Act) :- intentional_action(Act), not delegation_action(Act).

unintentional_action(appear_threatening).
unintentional_action(fall_in_love(Ch)) :- character(Ch).

% Intentions
intention(dead(X)) :- character(X).
intention(marry(X)) :- character(X).
intention(possessed_by(Obj, Subj)) :- character(Subj), object(Obj).