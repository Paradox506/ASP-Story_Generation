% Roles
role(secret_agent, "You are a secret agent. Your mission is to kill the mastermind.").

% Define the map
place(headquarters; dropbox; lobby; office; cache; courtyard).
connection(headquarters, dropbox).
connection(headquarters, courtyard).
connection(dropbox, courtyard).
connection(lobby, cache).
connection(lobby, office).
connection(cache, office).
guarded_connection(courtyard, lobby).

% Object attribute
attr(is_paper(dox)).
attr(papers_required(courtyard, lobby, dox)).
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
possible_action(move(Dest)) :- place(Dest).
possible_action(move_through_guards(Dest, Paper)) :- place(Dest), attr(possesable_obj(Paper)).
possible_action(kill(Victim, Weapon)) :- attr(is_person(Victim)), attr(is_weapon(Weapon)).
possible_action(pickup(Obj)) :- attr(possesable_obj(Obj)).