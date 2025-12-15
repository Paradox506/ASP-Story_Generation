astep(0..maxstep-1).
step(0..maxstep).
boolean(t;f).

% Uniqueness and Existence
:- not 1 {fl(at(Subj, L), T) : place(L)} 1, attr(locatable_obj(Subj)), step(T). 
:- not 1 {fl(alive(Subj, B), T) : boolean(B)} 1, attr(is_person(Subj)), step(T).
:- not 1 {fl(loaded(Obj, B), T) : boolean(B)} 1, attr(is_weapon(Obj)), step(T).
:- not 1 {fl(has(Subj, Obj, B), T) : boolean(B)} 1, attr(is_person(Subj)), attr(possesable_obj(Obj)), step(T).

% Actions
%% Move
fl(at(Subj, Dest), T+1) :- act(Subj, move(Dest), T),
                          attr(is_mobile(Subj)), 
                          fl(alive(Subj, t), T),
                          connection(Start, Dest),
                          fl(at(Subj, Start), T),
                          astep(T).

nonexec_feedback("Destination is the same at starting location", move(Subj, Dest), T) :- 
		act(Subj, move(Dest), T),
		Dest = Start, fl(at(Subj, Start), T).

nonexec_feedback("Destination isn't connected to starting location", move(Subj, Dest), T) :- 
		act(Subj, move(Dest), T),
		fl(at(Subj, Start), T),
		not connection(Start, Dest).

nonexec_feedback("The subject isn't alive", move(Subj, Dest), T) :- 
		act(Subj, move(Dest), T),
		not fl(alive(Subj, t), T).


%% Move_through_guards
fl(at(Subj, Dest), T+1) :- act(Subj, move_through_guards(Dest, Paper), T),
						  attr(is_mobile(Subj)), 
						  fl(alive(Subj, t), T),
						  fl(has(Subj, Paper, t), T),
						  attr(is_paper(Paper)), 
						  attr(papers_required(Start, Dest, Paper)),
                          guarded_connection(Start, Dest),
                          fl(at(Subj, Start), T),
                          astep(T).

nonexec_feedback("Destination is the same at starting location", move_through_guards(Subj, Dest, Paper), T) :- 
		act(Subj, move_through_guards(Dest, Paper), T),
		Dest = Start, fl(at(Subj, Start), T).

nonexec_feedback("Destination isn't connected to starting location with guards", move_through_guards(Subj, Dest, Paper), T) :- 
		act(Subj, move_through_guards(Dest, Paper), T),
		fl(at(Subj, Start), T),
		not guarded_connection(Start, Dest).

nonexec_feedback("The subject isn't alive", move_through_guards(Subj, Dest, Paper), T) :- 
		act(Subj, move_through_guards(Dest, Paper), T),
		not fl(alive(Subj, t), T).

nonexec_feedback("The subject does not have the paper", move_through_guards(Subj, Dest, Paper), T) :- 	
		act(Subj, move_through_guards(Dest, Paper), T),
		fl(has(Subj, Paper, f), T).

nonexec_feedback("The paper is not the required one", move_through_guards(Subj, Dest, Paper), T) :- 	
		act(Subj, move_through_guards(Dest, Paper), T),
		fl(at(Subj, Start), T),
		guarded_connection(Start, Dest),
		not attr(papers_required(Start, Dest, Paper)).

%% Kill
fl(alive(Victim, f), T+1) :- 
	act(Subj, kill(Victim, Weapon), T),
	attr(is_weapon(Weapon)),
	fl(at(Subj, L), T), fl(at(Victim, L), T),
	fl(has(Subj, Weapon, t), T), fl(loaded(Weapon, t), T).

nonexec_feedback("The subject does not possess the weapon", kill(Subj, Victim, Weapon), T) :- 
	act(Subj, kill(Victim, Weapon), T),
	not fl(has(Subj, Weapon, t), T).

nonexec_feedback("The item being used to kill is not a weapon", kill(Subj, Victim, Weapon), T) :- 
	act(Subj, kill(Victim, Weapon), T),
	not attr(is_weapon(Weapon)).

nonexec_feedback("The subject is not at the same location as the target", kill(Subj, Victim, Weapon), T) :- 
	act(Subj, kill(Victim, Weapon), T),
	fl(at(Subj, L1), T), fl(at(Victim, L2), T),
	L1 != L2.

nonexec_feedback("The weapon isn't loaded", kill(Subj, Victim, Weapon), T) :- 
	act(Subj, kill(Victim, Weapon), T),
	not fl(loaded(Weapon, t), T).

%% Pickup
fl(has(Subj, Obj, t), T+1) :-
	act(Subj, pickup(Obj), T),
	fl(at(Subj, L), T), fl(at(Obj, L), T),
	attr(possesable_obj(Obj)).

nonexec_feedback("The subject is not at the same location as the item", pickup(Subj, Obj), T) :- 
	act(Subj, pickup(Obj), T),
	fl(at(Subj, L1), T), fl(at(Obj, L2), T),
	L1 != L2.

% Inertia
{fl(at(Subj, L), T+1)} :- fl(at(Subj, L), T), astep(T).
{fl(alive(Subj, B), T+1)} :- fl(alive(Subj, B), T), astep(T).
{fl(loaded(Obj, B), T+1)} :- fl(loaded(Obj, B), T), astep(T).
{fl(has(Subj, It, B), T+1)} :- fl(has(Subj, It, B), T), astep(T).

% No Concurrency
:- act(Subj, X, T), act(Subj, Y, T), X != Y. 

% Actions are exogenous
{act(Subj, Act, T) : possible_action(Act)} 1 :- attr(is_mobile(Subj)), astep(T).

%:- nonexec_feedback(F, Act, T).
%:- not fl_alive(mastermind, f, maxstep).
%:- not act_pickup(secret_agent, gun, 0).
%:- not act_move(secret_agent, dropbox, 1).
%:- not act_pickup(secret_agent, dox, 2).
%:- not act_move(secret_agent, courtyard, 3).
%:- not act_move_through_guards(secret_agent, lobby, dox, 4).

#show act/3.