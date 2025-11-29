astep(0..maxstep-1).
step(0..maxstep).
boolean(t;f).

% Uniqueness and Existence
:- not 1 {fl(at(Subj, L), T) : place(L)} 1, character(Subj), step(T). 
:- not 1 {fl(alive(Subj, B), T) : boolean(B)} 1, character(Subj), step(T).
:- not 1 {fl(dying(Subj, B), T) : boolean(B)} 1, character(Subj), step(T).
:- not 1 {fl(has(Subj, Obj, Qty), T) : quantity(Qty)} 1, object(Obj), character(Subj), step(T).
:- not 1 {intends(Subj, I, B, T) : boolean(B)} 1, intention(I), character(Subj), step(T).

% Inertia
{fl(at(Subj, L), T+1)} :- fl(at(Subj, L), T), astep(T).
{fl(alive(Subj, B), T+1)} :- fl(alive(Subj, B), T), astep(T).
{fl(dying(Subj, B), T+1)} :- fl(dying(Subj, B), T), astep(T).
{fl(has(Subj, It, Qty), T+1)} :- fl(has(Subj, It, Qty),  T), astep(T).
{intends(Subj, I, B, T+1)} :- intends(Subj, I, B, T), astep(T).

% Unexecuted intentional actions
planned_act(Subj, Act, I, T) :- act(Subj, Act, I, T).
planned_act(Subj, Act, I, T) :- unexec_act(Subj, Act, I, T).

% Actions
%% Move
%%% Causality
fl(at(Subj, Dest), T+1) :- act(Subj, move(Dest), I, T),
						  intends(Subj, I, t, T),
                          character(Subj), 
                          fl(alive(Subj, t), T),
                          connection(Start, Dest),
                          fl(at(Subj, Start), T),
                          astep(T).

nonexec_feedback("Destination isn't connected to starting location", move(Subj, Dest), T) :- 
		act(Subj, move(Dest), I, T),
		fl(at(Subj, Start), T),
		not connection(Start, Dest).

nonexec_feedback("Destination is the same as starting location", act(Subj, move(Dest), T)) :- 
		act(Subj, move(Dest), I, T),
		Dest = Start, fl(at(Subj, Start), T).

nonexec_feedback("The subject isn't alive", act(Subj, move(Dest), T)) :- 
		act(Subj, move(Dest), I, T),
		not fl(alive(Subj, t), T).

%%% Intentionality
justified(Subj, alive(Subj, t), I, T1) :- planned_act(Subj, move(Dest), I, T), T1 <= T, step(T1).
justified(Subj, at(Subj, Start), I, T1) :- planned_act(Subj, move(Dest), I, T), fl(at(Subj, Start), T), connection(Start, Dest), T1 <= T, step(T1). 
justification_needed(Subj, at(Subj, Dest), I, T+1) :- planned_act(Subj, move(Dest), I, T).

%%% Conflict
% By moving to Dest, the subject of this action threatens another character C2's intention I2, if the subject was at a different location D2 under the intention of C2, and C2 still currently intends the subject to be at D2
%threaten(Subj, I, C2, I2, move(Dest), at(Subj, D2), T) :- planned_act(Subj, move(Dest), I, T),
%											intends(C2, I2, t, T),
%											justified(C2, at(Subj, D2), I2, T),
%										    D2 != Dest.

%% Snakebite
%%% Causality
fl(dying(Subj, t), T+1) :- act(Subj, snakebite, T),
                          character(Subj), 
                          fl(alive(Subj, t), T),
                          astep(T).

intends(Subj, alive(Subj), t, T+1) :- act(Subj, snakebite, T),
                          character(Subj), 
                          fl(alive(Subj, t), T),
                          astep(T).

intends(Parent, alive(Subj), t, T+1) :- act(Subj, snakebite, T),
                          character(Subj), 
                          attr(is_parent_of(Parent, Subj)),
                          fl(alive(Subj, t), T),
                          fl(alive(Parent, t), T),
                          astep(T).

nonexec_feedback("The subject is not alive", act(Subj, snakebite, T)) :- 
		act(Subj, snakebite, T),
        not fl(alive(Subj, t), T),
        astep(T).

%%% Conflict
% By getting a snake bite, the universe threatens another character C2's intention I2, if C2 currently intends the subject to be alive
% We don't count conflicts with the universe
%threaten(universe, none, C2, I2, snakebite, alive(Subj), T) :- act(Subj, snakebite, T),
%											intends(C2, I2, t, T),
%											justified(C2, alive(Subj, t), I2, T).
%threaten(universe, none, C2, alive(Subj), snakebite, alive(Subj, t), T) :- act(Subj, snakebite, T),
%											intends(C2, alive(Subj), t, T),
%											fl(alive(Subj, t), T).

%% Take
%%% Causality
fl(has(Subj, Obj, Qty + 1), T+1) :-
	fl(has(Subj, Obj, Qty), T),
	act(Subj, take(Obj, Ch), I, T),
	intends(Subj, I, t, T),
	fl(has(Ch, Obj, Qty1), T),
	fl(alive(Subj, t), T),
	fl(at(Subj, L), T), fl(at(Ch, L), T),
	Subj != Ch, Qty1 > 0.

fl(has(Ch, Obj, Qty1 - 1), T+1) :-
	act(Subj, take(Obj, Ch), I, T),
	intends(Subj, I, t, T),
	fl(has(Ch, Obj, Qty1), T),
	fl(alive(Subj, t), T),
	fl(at(Subj, L), T), fl(at(Ch, L), T),
	Subj != Ch, Qty1 > 0.

intends(Sheriff, dead(Subj), t, T+1) :-
	act(Subj, take(Obj, Ch), I, T),
	intends(Subj, I, t, T),
	fl(has(Ch, Obj, Qty), T), Qty > 0,
	fl(alive(Subj, t), T),
	fl(at(Subj, L), T), fl(at(Ch, L), T),
	Subj != Ch,
	attr(is_sheriff(Sheriff)).

intends(Owner, possessed_by(Obj, Owner), t, T+1) :-
	act(Subj, take(Obj, Ch), I, T),
	intends(Subj, I, t, T),
	fl(has(Ch, Obj, Qty), T), Qty = 1,
	fl(alive(Subj, t), T),
	fl(at(Subj, L), T), fl(at(Ch, L), T),
	Subj != Ch,
	attr(belongs_to(Obj, Owner)).

nonexec_feedback("The target does not have more of this item", act(Subj, take(Obj, Ch), I, T)) :-
	act(Subj, take(Obj, Ch), I, T),
	fl(has(Ch, Obj, Qty1), T),
	Qty1 <= 0.

nonexec_feedback("The subject isn't alive", act(Subj, take(Obj, Ch), I, T)) :-
	act(Subj, take(Obj, Ch), I, T),
	not fl(alive(Subj, t), T).

nonexec_feedback("Cannot steal from other agent when the merchant still has medicine", act(Subj, take(Obj, Ch), I, T)) :-
	planned_act(Subj, take(Obj, Ch), I, T), not attr(is_merchant(Ch)), fl(has(Ch2, It, Qty), T), Qty > 0, attr(is_merchant(Ch2)), attr(is_medicine(It)),
	not fl(alive(Subj, t), T).

nonexec_feedback("The subject is the same as the victim", act(Subj, take(Obj, Ch), I, T)) :-
	act(Subj, take(Obj, Ch), I, T),
	Subj == Ch.

nonexec_feedback("The subject and the target is not at the same location", act(Subj, take(Obj, Ch), I, T)) :-
	act(Subj, take(Obj, Ch), I, T),
	fl(at(Subj, L1), T), fl(at(Ch, L2), T),
	L1 != L2.

nonexec_feedback("The object is not possessed by the target", act(Subj, take(Obj, Ch), I, T)) :-
	act(Subj, take(Obj, Ch), I, T),
	fl(has(Ch, Obj, Qty), T), Qty <= 0.

justified(Subj, has(Ch, Obj, 1), I, T1) :-
                planned_act(Subj, take(Obj, Ch), I, T),
                T1 <= T, step(T1).

justified(Subj, at(Subj, L), I, T1) :-
               planned_act(Subj, take(Obj, Ch), I, T), fl(at(Ch, L), T),
               T1 <= T, step(T1).

justified(Subj, alive(Subj, t), I, T1) :-
               planned_act(Subj, take(Obj, Ch), I, T),
               T1 <= T, step(T1).

justification_needed(Subj, has(Subj, Obj, 1), I, T+1) :- planned_act(Subj, take(Obj, Ch), I, T), I != possessed_by(Obj, Subj).

%%% Conflict
% By taking item Obj from Ch, the subject of this action threatens another character C2's intention I2, if C2 intends Ch to have the object
threaten(Subj, I, C2, I2, take(Obj, Ch), has(Ch, Obj, 1), T) :- planned_act(Subj, take(Obj, Ch), I, T),
											intends(C2, I2, t, T),
											Subj != Ch,
											justified(C2, has(Ch, Obj, 1), I2, T+1).

threaten(Subj, I, C2, possessed_by(Obj, Ch), take(Obj, Ch), has(Ch, Obj, 1), T+1) :- planned_act(Subj, take(Obj, Ch), I, T),
											Subj != Ch,
											intends(C2, possessed_by(Obj, Ch), t, T).


%% Kill
%%% Causality
fl(alive(Victim, f), T+1) :- 
	act(Subj, kill(Victim), I, T),
	intends(Subj, I, t, T),
	attr(is_armed(Subj)),
	fl(alive(Subj, t), T),
	fl(alive(Victim, t), T),
	fl(at(Subj, L), T), fl(at(Victim, L), T).

nonexec_feedback("The subject is not at the same location as the target", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	fl(at(Subj, L1), T), fl(at(Victim, L2), T),
	L1 != L2.

nonexec_feedback("The subject is not alive", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	fl(alive(Victim, f), T).

nonexec_feedback("The victim is not alive", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	fl(alive(Subj, f), T).

nonexec_feedback("The subject is not armed", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	not attr(is_armed(Subj)).

%%% Intentionality
justified(Subj, alive(Subj, t), I, T1) :- planned_act(Subj, kill(Victim), I, T), intends(Subj, I, t, T), T1 <= T, step(T1).

justified(Subj, at(Subj, L), I, T1) :- planned_act(Subj, kill(Victim), I, T), intends(Subj, I, t, T), fl(at(Victim, L), T),
					   T1 <= T, step(T1).

% Killing Victim justifies an intention where Victim ends up not alive
justified(Subj, alive(Victim, f), I, T1) :- planned_act(Subj, kill(Victim), I, T),
                                            intends(Subj, I, t, T),
                                            T1 <= T, step(T1).

justification_needed(Subj, alive(Victim, f), I, T+1) :- planned_act(Subj, kill(Victim), I, T), I != dead(Victim).

%%% Conflict
% By killing Victim, the subject of this action threatens another character C2's intention I2, if C2 currently intends Victim to be alive
threaten(Subj, I, C2, I2, kill(Victim), alive(Victim), T) :- planned_act(Subj, kill(Victim), I, T),
											intends(C2, I2, t, T),
											justified(C2, alive(Victim, t), I2, T+1).

threaten(Subj, I, C2, alive(Victim), kill(Victim), alive(Victim), T) :- planned_act(Subj, kill(Victim), I, T),
											intends(C2, alive(Victim, t), t, T).


%% Heal
%%% Causality
fl(dying(Target, f), T+1) :- 
	act(Subj, heal(Target, It), I, T),
	fl(has(Subj, It, Qty), T), Qty > 0,
	intends(Subj, I, t, T),attr(is_medicine(It)),
	fl(alive(Subj, t), T),
	fl(alive(Target, t), T),
	fl(dying(Target, t), T),
	fl(at(Subj, L), T), fl(at(Target, L), T).

intends(Target, alive(Target), f, T+1) :-
	act(Subj, heal(Target, It), I, T),
	fl(has(Subj, It, Qty), T), Qty > 0,
	intends(Subj, I, t, T),attr(is_medicine(It)),
	fl(alive(Subj, t), T),
	fl(alive(Target, t), T),
	fl(dying(Target, t), T),
	fl(at(Subj, L), T), fl(at(Target, L), T).

fl(has(Subj, It, Qty-1), T+1) :- 
	act(Subj, heal(Target, It), I, T),
	fl(has(Subj, It, Qty), T), Qty > 0,
	intends(Subj, I, t, T),
	attr(is_medicine(It)),
	fl(alive(Subj, t), T),
	fl(alive(Target, t), T),
	fl(dying(Target, t), T),
	fl(at(Subj, L), T), fl(at(Target, L), T).

nonexec_feedback("The subject is not at the same location as the target", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	fl(at(Subj, L1), T), fl(at(Target, L2), T),
	L1 != L2.

nonexec_feedback("The subject is not alive", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	not fl(alive(Subj, t), T).

nonexec_feedback("The target does not need to be healed", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	not fl(dying(Target, t), T).

nonexec_feedback("The target is not alive", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	not fl(alive(Target, t), T).

nonexec_feedback("The item is not a medicine", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	not attr(is_medicine(It)).

nonexec_feedback("The subject does not have the medicine", act(Subj, heal(Target, It), T)) :- 
	act(Subj, heal(Target, It), I, T),
	fl(has(Subj, It, Qty), T), Qty <= 0.


%%% Intentionality
justified(Subj, alive(Subj, t), I, T1) :- planned_act(Subj, heal(Target, It), I, T),
										  intends(Subj, I, t, T), T1 <= T, step(T1).
										  

justified(Subj, at(Subj, L), I, T1) :- planned_act(Subj, heal(Target, It), I, T), fl(at(Target, L), T),
										  intends(Subj, I, t, T), T1 <= T, step(T1), Target != Subj.

justified(Subj, alive(Target, t), I, T1) :- planned_act(Subj, heal(Target, It), I, T),
										  intends(Subj, I, t, T), T1 <= T, step(T1).

justified(Subj, has(Subj, It, 1), I, T1) :- planned_act(Subj, heal(Target, It), I, T),
										  intends(Subj, I, t, T), T1 <= T, step(T1).

justification_needed(Subj, alive(Target, t), I, T+1) :- planned_act(Subj, heal(Target, It), I, T), I != alive(Target).

%%% Conflict
% By healing the target, the subject of this action threatens another character C2's intention I2, if C2 currently intends the target to be dead
threaten(Subj, I, C2, I2, heal(Target, It), dead(Target), T) :- planned_act(Subj, heal(Target, It), I, T),
											intends(C2, I2, t, T),
											justified(C2, alive(Target, f), I2, T+1).

threaten(Subj, I, C2, dead(Target), heal(Target), dead(Target), T) :- planned_act(Subj, heal(Target, It), I, T),
											intends(C2, dead(Target), t, T).

% No Concurrency
% No character can take two actions at the same timestep
:- act(Subj, X, T), act(Subj, Y, T), X != Y. 
:- act(Subj, X, I1, T), act(Subj, Y, I2, T), X != Y. 
%:- unexec_act(Subj, X, T), unexec_act(Subj, Y, T), X != Y. 
:- unexec_act(Subj, X, I1, T), unexec_act(Subj, Y, I2, T), X != Y. 
% No two characters can take actions at the same timestep
:- act(Subj1, X, T), act(Subj2, Y, T), Subj1 != Subj2. 
:- act(Subj1, X, I1, T), act(Subj2, Y, I2, T), Subj1 != Subj2. 
%:- unexec_act(Subj1, X, T), unexec_act(Subj2, Y, T), Subj1 != Subj2. 
:- unexec_act(Subj1, X, I1, T), unexec_act(Subj2, Y, I2, T), Subj1 != Subj2. 
% Intentional actions and unintentional actions cannot both happen at the same timestep
:- act(Subj1, X, T), act(Subj2, Y, I, T).
:- act(Subj1, X, T), unexec_act(Subj2, Y, I, T).
:- act(Subj1, X, I1, T), unexec_act(Subj2, Y, I2, T).
% No executed actions and unexecuted actions at the same timestep
:- act(Subj1, X, I1, T), unexec_act(Subj2, Y, I2, T).

% Actions are exogenous
%{act(Subj, Act, T) : unintentional_action(Act)} 1 :- character(Subj), astep(T).
%{act(Subj, Act, I, T) : intentional_action(Act), intention(I)} 1 :- character(Subj), intends(Subj, I, t, T), astep(T).
%{unexec_act(Subj, Act, I, T) : intentional_action(Act), intention(I)} 1 :- character(Subj), intends(Subj, I, t, T), astep(T).

% Actions all have to be intentional
:- planned_act(Subj, ACT, I, T), intends(Subj, I, f, T).

% No open commitment frame
unjustified(Subj, FL, I, T) :- justification_needed(Subj, FL, I, T), not justified(Subj, FL, I, T).
open_commitment_frame(Subj, I) :- unjustified(Subj, FL, I, T).
:- open_commitment_frame(_, _).

% Non non-executable actions
:- nonexec_feedback(_, _).

% Plan should contain conflict
% Conflict happens when either P holds at T, or Act is actually executed
conflict(C1, I1, C2, I2, Act) :- threaten(C1, I1, C2, I2, Act, P, T).

%:- not conflict(_, _, _, _, _).

%:- not act(agent_0, snakebite, 0).
%:- not act(agent_0, move(l0_1), _, 1).
%:- not act(agent_0, move(l1_1), _, 2).
%:- not act(agent_0, move(l1_2), _, 3).
%:- not act(agent_0, move(gen_store), _, 4).
%:- not act(agent_0, take(meds,carl), _, 5).
%:- not act(agent_0, heal(agent_0,meds), _, 6).


#show nonexec_feedback/2.
%#show attr/1.
%#show justified/4.
%#show fl/2.
#show unjustified/4.
%#show justification_needed/4.
%#show open_commitment_frame/2.
#show act/3.
#show act/4.
#show unexec_act/4.
%#show hank_fl_6/1.
#show conflict/5.
#show threaten/7.
