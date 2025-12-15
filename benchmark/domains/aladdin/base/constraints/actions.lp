astep(0..maxstep-1).
step(0..maxstep).
boolean(t;f).

% Uniqueness and Existence
:- not 1 {fl(at(Subj, L), T) : place(L)} 1, character(Subj), step(T). 
:- not 1 {fl(alive(Subj, B), T) : boolean(B)} 1, character(Subj), step(T).
:- not 1 {fl(possessed_by(Obj, Subj), T) : character(Subj)} 1, object(Obj), step(T).
:- not 1 {fl(in_love_with(Ch1, Ch2, B), T) : boolean(B)} 1, character(Ch1), character(Ch2), step(T).
:- not 1 {fl(married_with(Ch1, Ch2, B), T) : boolean(B)} 1, character(Ch1), character(Ch2), step(T). 

:- not 1 {intends(Subj, I, B, T) : boolean(B)} 1, intention(I), character(Subj), step(T).

% Actions
%% Move
fl(at(Subj, Dest), T+1) :- act(Subj, move(Dest), I, T),
						  intends(Subj, I, t, T),
                          character(Subj), 
                          fl(alive(Subj, t), T),
                          fl(at(Subj, Start), T),
                          attr(is_knight(Subj)),
                          astep(T).

fl(at(galileo, Dest), T+1) :- act(Subj, move(Dest), I, T),
						  intends(Subj, I, t, T),
						  fl(possessed_by(lamp, Subj), T),
                          character(Subj), 
                          fl(alive(Subj, t), T),
                          fl(at(Subj, Start), T),
                          astep(T).

nonexec_feedback("Destination is the same as starting location", act(Subj, move(Dest), T)) :- 
		act(Subj, move(Dest), I, T),
		Dest = Start, fl(at(Subj, Start), T).

nonexec_feedback("The subject isn't alive", act(Subj, move(Dest), T)) :- 
		act(Subj, move(Dest), I, T),
		not fl(alive(Subj, t), T).

justified(Subj, alive(Subj, t), I, T1) :- act(Subj, move(Dest), I, T), T1 <= T, step(T1).
justified(Subj, at(Subj, Start), I, T1) :- act(Subj, move(Dest), I, T), fl(at(Subj, Start), T), T1 <= T, step(T1).
justification_needed(Subj, at(Subj, Dest), I, T+1) :- act(Subj, move(Dest), I, T).

%% Kill
fl(alive(Victim, f), T+1) :- 
	act(Subj, kill(Victim), I, T),
	intends(Subj, I, t, T),
	attr(is_knight(Subj)),
	fl(alive(Subj, t), T),
	fl(at(Subj, L), T), fl(at(Victim, L), T).

nonexec_feedback("The subject is not at the same location as the target", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	fl(at(Subj, L1), T), fl(at(Victim, L2), T),
	L1 != L2.

nonexec_feedback("The subject is not alive", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	fl(alive(Subj, f), T).

nonexec_feedback("The subject is not a knight", act(Subj, kill(Victim), T)) :- 
	act(Subj, kill(Victim), I, T),
	not attr(is_knight(Subj)).

justified(Subj, alive(Subj, t), I, T1) :- act(Subj, kill(Victim), I, T), T1 <= T, step(T1).
justified(Subj, at(Subj, L), I, T1) :- act(Subj, kill(Victim), I, T), fl(at(Victim, L), T), T1 <= T, step(T1).
justification_needed(Subj, alive(Victim, f), I, T+1) :- act(Subj, kill(Victim), I, T), I != dead(Victim).

%% Summon Genie and cast a love spell
fl(in_love_with(Target, Lover, t), T+1) :-
	act(Subj, cast_love_spell(Target, Lover), I, T),
	intends(Subj, I, t, T),
	fl(possessed_by(lamp, Subj), T),
	fl(alive(Subj, t), T),
	fl(alive(galileo, t), T).

nonexec_feedback("The subject does not hava the lamp", act(Subj, cast_love_spell(Target, Lover), T)) :- 
	act(Subj, cast_love_spell(Target, Lover), I, T),
	not fl(possessed_by(lamp, Subj), T).

nonexec_feedback("The subject is dead", act(Subj, cast_love_spell(Target, Lover), T)) :- 
	act(Subj, cast_love_spell(Target, Lover), I, T),
	not fl(alive(Subj, t), T).

nonexec_feedback("Genie is dead", act(Subj, cast_love_spell(Target, Lover), T)) :- 
	act(Subj, cast_love_spell(Target, Lover), I, T),
	not fl(alive(galileo, t), T).

justified(Subj, possessed_by(lamp, Subj), I, T1) :- act(Subj, cast_love_spell(Target, Lover), I, T), T1 <= T, step(T1).
justified(Subj, alive(Subj, t), I, T1) :- act(Subj, cast_love_spell(Target, Lover), I, T), T1 <= T, step(T1).
justified(Subj, alive(galileo, t), I, T1) :- act(Subj, cast_love_spell(Target, Lover), I, T), T1 <= T, step(T1).
justification_needed(Subj, in_love_with(Target, Lover, t), I, T+1) :- act(Subj, cast_love_spell(Target, Lover), I, T).

%% Marry
fl(married_with(Ch1, Ch2, t), T+1) :- 
	act(Ch1, marry(Ch2), I, T),
	intends(Subj, I, t, T),
	fl(in_love_with(Ch1, Ch2, t), T),
	fl(in_love_with(Ch2, Ch1, t), T),
	fl(at(Ch1, L), T), fl(at(Ch2, L), T).

nonexec_feedback("The characters do not love each other to get married", act(Ch1, marry(Ch2), T)) :- 
	act(Ch1, marry(Ch2), I, T),
	not fl(in_love_with(Ch1, Ch2, t), T).

nonexec_feedback("The characters do not love each other to get married", act(Ch1, marry(Ch2), T)) :- 
	act(Ch1, marry(Ch2), I, T),
	not fl(in_love_with(Ch2, Ch1, t), T).

nonexec_feedback("The characters are not at the same location to get married", act(Ch1, marry(Ch2), T)) :- 
	act(Ch1, marry(Ch2), I, T),
	fl(at(Ch1, L1), T), fl(at(Ch2, L2), T), L1 != L2.

justified(Subj, in_love_with(Subj, Ch2, t), I, T1) :- act(Subj, marry(Ch2), I, T), T1 <= T, step(T1).
justified(Subj, in_love_with(Ch2, Subj, t), I, T1) :- act(Subj, marry(Ch2), I, T), T1 <= T, step(T1).
justified(Subj, at(Subj, L), I, T1) :- act(Subj, marry(Ch2), I, T), fl(at(Ch2, L), T), T1 <= T, step(T1).
justified(Subj, at(Ch2, L), I, T1) :- act(Subj, marry(Ch2), I, T), fl(at(Ch2, L), T), T1 <= T, step(T1).
justification_needed(Subj, married_with(Subj, Ch2, t), I, T+1) :- act(Subj, marry(Ch2), I, T), I != marry(Ch2).

%% Pillage
fl(possessed_by(Obj, Pillager), T+1) :-
	act(Pillager, pillage(Body, Obj), I, T),
	intends(Subj, I, t, T),
	fl(possessed_by(Obj, Body), T),
	fl(alive(Body, f), T),
	fl(alive(Pillager, t), T),
	fl(at(Pillager, L), T), fl(at(Body, L), T).

nonexec_feedback("The target isn't dead", act(Pillager, pillage(Body, Obj), T)) :-
	act(Pillager, pillage(Body, Obj), I, T),
	not fl(alive(Body, f), T).

nonexec_feedback("The pillager is dead", act(Pillager, pillage(Body, Obj), T)) :-
	act(Pillager, pillage(Body, Obj), I, T),
	not fl(alive(Pillager, t), T).

nonexec_feedback("The pillager and the target is not at the same location", act(Pillager, pillage(Body, Obj), T)) :-
	act(Pillager, pillage(Body, Obj), I, T),
	fl(at(Pillager, L1), T), fl(at(Body, L2), T),
	L1 != L2.

nonexec_feedback("The object is not possessed by the target", act(Pillager, pillage(Body, Obj), T)) :-
	act(Pillager, pillage(Body, Obj), I, T),
	not fl(possessed_by(Obj, Body), T).


justified(Pillager, possessed_by(Obj, Body), I, T1) :- act(Pillager, pillage(Body, Obj), I, T), T1 <= T, step(T1).
justified(Pillager, alive(Body, f), I, T1) :- act(Pillager, pillage(Body, Obj), I, T), T1 <= T, step(T1).
justified(Pillager, at(Pillager, L), I, T1) :- act(Pillager, pillage(Body, Obj), I, T), fl(at(Body, L), T), T1 <= T, step(T1).
justification_needed(Pillager, possessed_by(Obj, Pillager), I, T+1) :- act(Pillager, pillage(Body, Obj), I, T).

%% Give
fl(possessed_by(Obj, Givee), T+1) :-
	act(Giver, give(Givee, Obj), I, T),
	intends(Subj, I, t, T),
	fl(possessed_by(Obj, Giver), T),
	fl(alive(Giver, t), T),
	fl(alive(Givee, t), T),
	fl(at(Giver, L), T), fl(at(Givee, L), T).

nonexec_feedback("The object is not possessed by the giver", act(Giver, give(Givee, Obj), T)) :-
	act(Giver, give(Givee, Obj), I, T),
	not fl(possessed_by(Obj, Giver), T).

nonexec_feedback("The giver and the givee is not at the same location", act(Giver, give(Givee, Obj), T)) :-
	act(Giver, give(Givee, Obj), I, T),
	fl(at(Giver, L1), T), fl(at(Givee, L2), T),
	L1 != L2.

justified(Giver, possessed_by(Obj, Giver), I, T1) :- act(Giver, give(Givee, Obj), I, T), T1 <= T, step(T1).
justified(Giver, alive(Giver, t), I, T1) :- act(Giver, give(Givee, Obj), I, T), T1 <= T, step(T1).
justified(Giver, alive(Givee, t), I, T1) :- act(Giver, give(Givee, Obj), I, T), T1 <= T, step(T1).
justified(Giver, at(Giver, L), I, T1) :- act(Giver, give(Givee, Obj), I, T), fl(at(Givee, L), T), T1 <= T, step(T1).
justification_needed(Giver, possessed_by(Obj, Givee), I, T+1) :- act(Giver, give(Givee, Obj), I, T), I != possessed_by(Obj, Givee).

%% Order to kill
intends(Knight, dead(Subj), t, T+1) :-
	act(Subj, order_to_kill(Knight, Victim), I, T),
	intends(Subj, I, t, T),
	attr(is_loyal_to(Knight, Subj)).

intends(Subj, dead(Subj), f, T+1) :-
	act(Subj, order_to_kill(Knight, Victim), I, T),
	attr(is_loyal_to(Knight, Subj)).

justification_needed(Subj, alive(Victim, f), I, T+1) :- act(Subj, order_to_kill(Knight, Victim), I, T), I != dead(Victim).

nonexec_feedback("The knight is not loyal to the subject", act(Subj, order_to_kill(Knight, Victim, T))) :- 
	act(Subj, order_to_kill(Knight, Victim), T),
	not attr(is_loyal_to(Knight, Subj)).

%% Order to obtain
intends(Knight, possessed_by(Obj, Subj), t, T+1) :-
	act(Subj, order_to_obtain(Knight, Obj), I, T),
	intends(Subj, I, t, T),
	attr(is_loyal_to(Knight, Subj)).

intends(Subj, possessed_by(Obj, Subj), f, T+1) :-
	act(Subj, order_to_obtain(Knight, Obj), I, T),
	attr(is_loyal_to(Knight, Subj)).

nonexec_feedback("The knight is not loyal to the subject", act(Subj, order_to_obtain(Knight, Obj, T))) :- 
	act(Subj, order_to_obtain(Knight, Obj), T),
	not attr(is_loyal_to(Knight, Subj)).

justification_needed(Subj, possessed_by(Obj, Subj), I, T+1) :- act(Subj, order_to_obtain(Knight, Obj), I, T), I != possessed_by(Obj, Subj).

%% Appear threatening
intends(Ch, dead(Subj), t, T+1) :-
	act(Subj, appear_threatening, T),
	attr(is_scary(Subj)),
	character(Ch), Ch != Subj.

nonexec_feedback("The subject is not scary", act(Subj, appear_threatening, T)) :- 
	act(Subj, appear_threatening, T),
	not attr(is_scary(Subj)).

%% Fall in love
fl(in_love_with(Subj, Target, t), T+1) :-
	act(Subj, fall_in_love(Target), T),
	Subj != polly,
	Target != Subj.

intends(Subj, marry(Target), t, T+1) :-
	act(Subj, fall_in_love(Target), T),
	Target != Subj.

% Inertia
{fl(at(Subj, L), T+1)} :- fl(at(Subj, L), T), astep(T).
{fl(alive(Subj, B), T+1)} :- fl(alive(Subj, B), T), astep(T).
{fl(possessed_by(It, Subj), T+1)} :- fl(possessed_by(It, Subj),  T), astep(T).
{fl(in_love_with(Ch1, Ch2, B), T+1)} :-
fl(in_love_with(Ch1, Ch2, B), T), astep(T).
{fl(married_with(Ch1, Ch2, B), T+1)} :-
fl(married_with(Ch1, Ch2, B), T), astep(T).

{intends(Subj, I, B, T+1)} :- intends(Subj, I, B, T), astep(T).

% No Concurrency
:- act(Subj, X, T), act(Subj, Y, T), X != Y. 
:- act(Subj1, X, T), act(Subj2, Y, T), Subj1 != Subj2. 
:- act(Subj, X, I1, T), act(Subj, Y, I2, T), X != Y. 
:- act(Subj, X, I1, T), act(Subj, Y, I2, T), I1 != I2.
:- act(Subj1, X, I1, T), act(Subj2, Y, I2, T), Subj1 != Subj2. 
:- act(Subj1, X, T), act(Subj2, Y, I, T).

% Actions are exogenous
%{act(Subj, Act, T) : unintentional_action(Act)} 1 :- character(Subj), astep(T).
%{act(Subj, Act, I, T) : non_delegation_action(Act), intention(I)} 1 :- character(Subj), intends(Subj, I, t, T), astep(T).
%{act(Subj, order_to_kill(Knight, Victim), I, T) : intention(I), character(Victim)} 1 :- attr(is_loyal_to(Knight, Subj)), intends(Subj, I, t, T), astep(T).
%{act(Subj, order_to_obtain(Knight, lamp), I, T) : intention(I)} 1 :- attr(is_loyal_to(Knight, Subj)), intends(Subj, I, t, T), astep(T).

% Actions all have to be intentional
:- act(Subj, ACT, I, T), intends(Subj, I, f, T).

% No open commitment frame
unjustified(Subj, FL, I, T) :- justification_needed(Subj, FL, I, T), not justified(Subj, FL, I, T).
open_commitment_frame(Subj, I) :- unjustified(Subj, FL, I, T).
:- open_commitment_frame(_, _).

% Non non-executable actions
:- nonexec_feedback(_, _).

%:- not act(david, appear_threatening, 0).
%:- not act(alice, kill(david), _, 1).
%:- not act(alice, pillage(david,lamp), _, 2).
%:- not act(alice, give(kamy,lamp), _, 3).
%:- not act(kamy, cast_love_spell(kamy,polly), _, 4).
%:- not act(polly, fall_in_love(kamy), 5).
%:- not act(kamy, marry(polly), _, 6).
%:- not act(alice, move(mountain), _, 7).
%:- not act(galileo, appear_threatening, 8).
%:- not act(alice, kill(galileo), _, 9).
%:- not fl(married_with(kamy, polly, t), 10).
%:- not fl(alive(galileo, f), 10).

%:- not act(david, appear_threatening, 0).
%:- not act(kamy, order_to_kill(alice, david), dead(david), 1).
%:- not act(alice, move(mountain), dead(david), 2).
%:- not act(alice, kill(david), dead(david), 3).
%:- not act(kamy, fall_in_love(polly), 4).
%:- not act(kamy, order_to_obtain(alice, lamp), marry(polly), 5).
%:- not act(alice, pillage(david, lamp), possessed_by(lamp, kamy), 6).
%:- not act(alice, move(castle), possessed_by(lamp, kamy), 7).
%:- not act(alice, give(kamy, lamp), possessed_by(lamp, kamy), 8).
%:- not act(kamy, cast_love_spell(polly, kamy), marry(polly), 9).
%:- not act(galileo, appear_threatening, 10).
%:- not act(kamy, order_to_kill(alice, galileo), dead(galileo), 11).
%:- not act(alice, kill(galileo), dead(galileo), 12).
%:- not act(kamy, marry(polly), marry(polly), 13).
%:- not fl(married_with(alice, polly, t), 14).

%:- not act(aladdin, fall_in_love(jasmine), 0).
%:- not act(aladdin, move(mountain), marry(jasmine), 1).
%:- not act(aladdin, kill(dragon), marry(jasmine), 2).
%:- not act(aladdin, pillage(dragon, lamp), marry(jasmine), 3).
%:- not act(aladdin, cast_love_spell(jasmine, aladdin), marry(jasmine), 4).
%:- not act(aladdin, move(castle), marry(jasmine), 5).
%:- not act(aladdin, marry(jasmine), marry(jasmine), 6).

%:- not act(Ch, cast_love_spell(Ch, jasmine), I, T), character(Ch), intention(I), step(T).
%:- not act(dragon, fall_in_love(jasmine), 0).
%:- not act(dragon, cast_love_spell(jasmine, dragon), marry(jasmine), 1).
%:- not act(dragon, move(castle), marry(jasmine), 2).
%:- not act(dragon, marry(jasmine), marry(jasmine), 3).

% act/3's are unintentional actions
#show act/3.
%#show fl/2.
% act/4's are intentioanl actions
#show act/4.
%#show intends/4.
#show unjustified/4.
#show open_commitment_frame/2.
#show nonexec_feedback/2.