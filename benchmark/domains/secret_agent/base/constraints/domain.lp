% Roles
role(secret_agent, "You are secret_agent. Your mission is to kill the mastermind.").

% Object attribute
attr(is_paper(dox)).
attr(papers_required(Start, End, dox)) :- guarded_connection(Start, End).
attr(is_person(secret_agent)).
attr(is_person(mastermind)).
attr(is_mobile(secret_agent)).
attr(is_weapon(gun)).
attr(locatable_obj(X)) :- attr(is_person(X)).
attr(locatable_obj(X)) :- attr(is_paper(X)).
attr(locatable_obj(X)) :- attr(is_weapon(X)).
attr(possesable_obj(X)) :- attr(is_weapon(X)).
attr(possesable_obj(X)) :- attr(is_paper(X)).

% Actions
possible_action(move(Dest)) :- place(Dest), Dest != nowhere.
possible_action(move_through_guards(Dest, dox)) :- place(Dest),  Dest != nowhere.
possible_action(kill(Victim, Weapon)) :- attr(is_person(Victim)), attr(is_weapon(Weapon)).
possible_action(pickup(Obj)) :- attr(possesable_obj(Obj)), Obj != dox.