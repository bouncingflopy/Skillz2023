from penguin_game import *
from math import ceil


class Penguin:
    def __init__(self, game, penguin_group, destination):
        self.game = game
        self.penguin_group = penguin_group
        self.destination = destination

    def should_accelerate(self):
        old_penguins = self.penguin_group.penguin_amount
        old_turns = self.penguin_group.turns_till_arrival
        new_penguins = old_penguins // self.game.acceleration_cost
        new_turns = ceil(old_turns / self.game.acceleration_factor)

        result = self.destination.calculate_accelerated(self.penguin_group, old_penguins, old_turns, new_penguins, new_turns)

        if result:
            for i, group in enumerate(self.destination.penguin_groups):
                if group == (self.penguin_group, old_penguins, old_turns):
                    self.destination.penguin_groups[i] = (self.penguin_group, new_penguins, new_turns)
            self.destination.calculate_penguin_groups()

        return result


class Ice:
    def __init__(self, game, ice):
        self.game = game
        self.ice = ice
        self.penguins_per_turn = self.ice.penguins_per_turn if self.ice.owner is not game.get_neutral() else 0

        self.penguin_groups = []  # Group, amount, turns
        self.changes = []  # turn, amount, owner
        self.extra = self.ice.penguin_amount

        self.changes_owner = False
        self.minimum = self.ice.penguin_amount
        self.minimum_turn = 0

        self.action = None
        self.cooperate = []  # For friends

        self.attackers = []  # For enemies
        self.target_enemy = None  # For friends
        self.attacked = False  # For enemies

    def calculate_penguin_groups(self):
        current_turn = 0
        current_amount = self.ice.penguin_amount
        current_owner = self.ice.owner
        penguins_per_turn = self.ice.penguins_per_turn

        for group, amount, turns in sorted(self.penguin_groups, key=lambda x: (x[2], x[1])):
            turns_passed = turns - current_turn
            if current_owner is not self.game.get_neutral():
                current_amount += turns_passed * penguins_per_turn
            current_turn = turns

            if group.owner is current_owner:
                current_amount += amount
            else:
                current_amount -= amount
                if current_amount < 0:
                    current_amount = -current_amount
                    current_owner = group.owner
                    self.changes_owner = True

            self.changes.append((current_turn, current_amount, current_owner))

    # def calculate_danger(self):
    #     attacks = []
    #
    #     for enemy in self.game.get_enemy_icebergs():
    #         my_attacks = []
    #
    #         power = 1
    #         while True:
    #             turns = 0
    #             penguins = enemy.penguin_amount
    #             distance = enemy.get_turns_till_arrival(self.ice)
    #             speed = 1
    #             current_power = 1
    #             while distance > 0:
    #                 distance -= speed
    #                 turns += 1
    #
    #                 if current_power < power:
    #                     current_power += 1
    #                     speed *= self.game.acceleration_factor
    #                     penguins //= self.game.acceleration_cost
    #
    #             my_attacks.append((penguins, turns))
    #
    #             if current_power < power:
    #                 break
    #
    #             power += 1
    #
    #         attacks.append((enemy, my_attacks))
    #
    #     danger = 0
    #     for enemy, attacks_list in attacks:
    #         my_danger = 0
    #         for penguins, turns in attacks_list:
    #             change = penguins - (turns * self.penguins_per_turn)
    #             if change > my_danger:
    #                 my_danger = change
    #         danger += my_danger
    #
    #     return int(danger)

    def calculate_extra(self):
        for _, amount, owner in self.changes:
            signed_amount = amount * (1 if owner is self.ice.owner else -1)
            if signed_amount < self.extra:
                self.extra = signed_amount

        if self.ice.is_icepital and self.changes_owner:
            self.extra = 0

        if self.changes_owner:
            for turn, amount, owner in self.changes:
                if owner is not self.ice.owner and -amount < self.minimum:
                    self.minimum = -amount
                    self.minimum_turn

        # self.extra = max([0, self.extra - self.calculate_danger()])

    def calculate_accelerated(self, penguin_group, old_penguins, old_turns, new_penguins, new_turns):
        penguin_groups = self.penguin_groups[:]
        for i, group in enumerate(penguin_groups):
            if group == (penguin_group, old_penguins, old_turns):
                penguin_groups[i] = (penguin_group, new_penguins, new_turns)

        current_turn = 0
        current_amount = self.ice.penguin_amount
        current_owner = self.ice.owner
        penguins_per_turn = self.ice.penguins_per_turn

        for group, amount, turns in sorted(penguin_groups, key=lambda x: (x[2], x[1])):
            turns_passed = turns - current_turn
            if current_owner is not self.game.get_neutral():
                current_amount += turns_passed * penguins_per_turn
            current_turn = turns

            if group.owner is current_owner:
                current_amount += amount
            else:
                current_amount -= amount
                if current_amount < 0:
                    current_amount = -current_amount
                    current_owner = group.owner

        return (current_owner is penguin_group.owner and (len(self.changes) == 0 or self.changes[-1][2] is not penguin_group.owner)) or (
                self.ice.is_icepital and self.ice.owner is self.game.get_myself() and self.minimum < 0 and self.minimum_turn < old_turns)

    def calculate_different_changes(self, owner, new_changes):
        penguin_groups = self.penguin_groups[:]
        for new_ice, new_penguins, new_turns in new_changes:
            penguin_groups.append((new_ice, new_penguins, new_turns))

        current_turn = 0
        current_amount = self.ice.penguin_amount
        current_owner = self.ice.owner
        penguins_per_turn = self.ice.penguins_per_turn

        for group, amount, turns in sorted(penguin_groups, key=lambda x: (x[2], x[1])):
            turns_passed = turns - current_turn
            if current_owner is not self.game.get_neutral():
                current_amount += turns_passed * penguins_per_turn
            current_turn = turns

            if group.owner is current_owner:
                current_amount += amount
            else:
                current_amount -= amount
                if current_amount < 0:
                    current_amount = -current_amount
                    current_owner = group.owner

        return current_owner is owner, current_amount

    def can_be_conquered_by(self, attacker, power):
        turns = 0
        penguins = attacker.extra
        distance = attacker.ice.get_turns_till_arrival(self.ice)
        speed = 1
        current_power = 1
        while distance > 0:
            distance -= speed
            turns += 1

            if current_power < power:
                current_power += 1
                speed *= self.game.acceleration_factor
                penguins //= self.game.acceleration_cost

        can_conquer, excess = self.calculate_different_changes(attacker.ice.owner, [(attacker.ice, penguins, turns)])

        if can_conquer:
            if excess > 1:
                penguins = attacker.extra - excess + 1
                for _ in range(current_power - 1):
                    penguins //= self.game.acceleration_cost
                can_conquer = self.calculate_different_changes(attacker.ice.owner, [(attacker.ice, penguins, turns)])[0]

                if can_conquer:
                    return True, attacker.extra - excess + 1, turns, current_power < power

            return True, attacker.extra, turns, current_power < power
        else:
            return False, None, None, current_power < power

    def calculate_best_power(self, enemy):
        power = 1
        stats = lambda x: enemy.can_be_conquered_by(self, x)  # can, amount, turns, max_power
        all_powers = []

        while True:
            results = stats(power)
            all_powers.append(results)
            power += 1
            if not results[3]:
                break

        least = None
        for p in all_powers:
            if p[0] and (least is None or p[2] < least[2]):
                least = p

        if least is None:
            return False, None, None, None
        else:
            return least[0], self, least[1], least[2]

    def optimize_cooperate_attack(self, attackers):
        if len(attackers) == 0:
            return False, []

        changes = {ice: (ice.ice, amount, turns) for ice, amount, turns in attackers}
        owner = self.game.get_myself()

        can_conquer, _ = self.calculate_different_changes(owner, list(changes.values()))

        if not can_conquer:
            return False, []

        changes_list = list(changes.values())
        for ice in sorted(list(changes.keys()), reverse=True, key=lambda x: x.ice.get_turns_till_arrival(self.ice)):
            new_changes = [change for change in changes_list if change is not changes[ice]]
            if self.calculate_different_changes(owner, new_changes)[0]:
                changes_list = new_changes

        return True, changes_list

    def get_turns_till_upgrade(self):
        cost = self.ice.upgrade_cost + self.extra
        turn = ceil(max([0, cost]) / self.ice.penguins_per_turn)
        extras = 0

        for change in self.changes:
            if change[0] < turn and change[2] is self.game.get_myself():
                extras += change[1]

        turn -= ceil(extras / self.ice.penguins_per_turn)

        return turn  # TODO - optimize this


def do_turn(game):
    # Check if caps exist
    if len(game.get_my_icepital_icebergs()) > 0 and len(game.get_enemy_icepital_icebergs()) > 0:
        cap = game.get_my_icepital_icebergs()[0]
    else:
        return None

    # Create Ices
    ices = {ice: Ice(game, ice) for ice in game.get_all_icebergs()}

    # Add penguins_groups to Ices
    for penguin_group in [penguin for penguin in game.get_all_penguin_groups() if not penguin.is_siege_group]:
        if penguin_group.destination is not game.get_cloneberg():
            ices[penguin_group.destination].penguin_groups.append((penguin_group, penguin_group.penguin_amount, penguin_group.turns_till_arrival))
        else:
            ices[penguin_group.source].penguin_groups.append((penguin_group, penguin_group.penguin_amount * game.cloneberg_multi_factor,
                                                              penguin_group.turns_till_arrival + game.cloneberg_max_pause_turns +
                                                              ceil(penguin_group.destination.get_turns_till_arrival(penguin_group.source) / penguin_group.current_speed)))

    # Calculate penguin_groups affect on Ices
    for ice in game.get_all_icebergs():
        ices[ice].calculate_penguin_groups()
        ices[ice].calculate_extra()

    # Create Penguins
    penguins = {penguin: Penguin(game, penguin, ices[penguin.destination]) for penguin in game.get_my_penguin_groups() if penguin.destination is not game.get_cloneberg() and not penguin.is_siege_group}

    # Accelerate Penguins
    for penguin in sorted([penguin for penguin in game.get_my_penguin_groups() if not penguin.is_siege_group], reverse=True, key=lambda x: x.turns_till_arrival):
        if penguin.destination is not game.get_cloneberg():
            if penguins[penguin].should_accelerate():
                penguin.accelerate()

    # Save cap
    if ices[cap].changes_owner:
        friends = sorted([friend for friend in game.get_my_icebergs() if friend is not cap and ices[friend].extra > 0], key=lambda x: x.get_turns_till_arrival(cap))
        needed = -ices[cap].minimum

        while len(friends) > 0 and needed > 0:
            friend = friends[0]
            send_amount = min(needed, ices[friend].extra)
            ices[friend].action = ("Send", cap, send_amount)

            needed -= send_amount
            del friends[0]

        if needed > 0:
            friends = sorted([friend for friend in game.get_my_icebergs() if friend is not cap], key=lambda x: x.get_turns_till_arrival(cap))
            while len(friends) > 0 and needed > 0:
                friend = friends[0]
                if ices[friend].action is not None:
                    needed += ices[friend].action[2]

                send_amount = friend.penguin_amount
                ices[friend].action = ("Send", cap, send_amount)

                needed -= send_amount
                del friends[0]

    # Find potential attackees
    attackable = [ice for ice in game.get_all_icebergs() if (ice.owner is not game.get_myself() and len(ices[ice].changes) == 0) or (len(ices[ice].changes) > 0 and ices[ice].changes[-1][2] is not game.get_myself())]

    # Find attackees
    for enemy in attackable:
        for ice in game.get_my_icebergs():
            if not ice.is_under_siege:
                if ice is not enemy:
                    if ices[ice].action is None and ices[ice].target_enemy is None:
                        best_power = ices[ice].calculate_best_power(ices[enemy])
                        if best_power[0]:
                            ices[enemy].attackers.append(best_power[1:])  # attacker, amount, turns
        ices[enemy].attackers = sorted(ices[enemy].attackers, key=lambda x: (x[2], x[1]))

    # Match attackers to attackees
    while True:
        options = [(ices[enemy], [attacker for attacker in ices[enemy].attackers if attacker[0].target_enemy is None])
                   for enemy in attackable if len([attacker for attacker in ices[enemy].attackers if attacker[0].target_enemy is None]) > 0]
        options = sorted(options, key=lambda x: (not x[0].ice.is_icepital, not ((len(x[0].changes) == 0 and x[0].ice.owner is game.get_enemy()) or (len(x[0].changes) > 0 and x[0].changes[-1][2] is game.get_enemy())), -x[0].ice.level, x[1][0][2], x[1][0][1]))

        if len(options) == 0:
            break

        best_option = options[0]
        best_option[0].attackers = []
        best_option[0].attacked = True
        best_option[1][0][0].target_enemy = (best_option[0], best_option[1][0][1], best_option[1][0][2])  # target, amount, turns

    # Find cooperate attackees
    options = []
    for enemy in attackable:
        if not ices[enemy].attacked:
            attackers = []
            for ice in game.get_my_icebergs():
                if not ice.is_under_siege:
                    if ice is not enemy:
                        if ices[ice].action is None and ices[ice].target_enemy is None and ices[ice].extra > 0:
                            attackers.append((ices[ice], ices[ice].extra, ice.get_turns_till_arrival(enemy)))

            can, attack = ices[enemy].optimize_cooperate_attack(attackers)  # list(attacker.ice, amount, turns)
            if can:
                options.append((enemy, attack))

    # Match attackers to attackees
    while True:
        options = [(ices[enemy], attack) for enemy, attack in options if all([ices[attacker].target_enemy is None for attacker, _, _ in attack])]
        options = sorted(options, key=lambda x: (not x[0].ice.is_icepital, not ((len(x[0].changes) == 0 and x[0].ice.owner is game.get_enemy()) or (len(x[0].changes) > 0 and x[0].changes[-1][2] is game.get_enemy())), -x[0].ice.level, sum([i for _, _, i in x[1]]), sum([i for _, i, _ in x[1]])))

        if len(options) == 0:
            break

        best_option = options[0]
        best_option[0].attackers = []
        best_option[0].attacked = True

        for attacker, amount, turns in best_option[1]:
            ices[attacker].target_enemy = (best_option[0], amount, turns)
            ices[attacker].cooperate = [ices[i] for i, _, _ in best_option[1]]

    # Create actions for Ices
    for ice in game.get_my_icebergs():
        if ices[ice].action is None:
            target = ices[ice].target_enemy
            best_move = None

            if target is not None and ices[ice].extra >= target[1] and ice.level < ice.upgrade_level_limit:
                if target[0].ice.owner is game.get_myself():
                    best_move = "Send"
                else:
                    turns = target[2]
                    turns_till_upgrade = max([0, ceil((ice.upgrade_cost - ices[ice].extra) / ice.penguins_per_turn)])
                    turns_delay = max([0, ceil((ice.upgrade_cost - ices[ice].extra - target[1]) / ice.penguins_per_turn)])

                    if turns_delay - turns > turns_till_upgrade:  # TODO - optimize this
                        best_move = "Send"
                    else:
                        best_move = "Upgrade"

            if target is not None and ices[ice].extra >= target[1] and (best_move is "Send" or best_move is None):
                ices[ice].action = ("Send", target[0].ice, int(target[1]))
            elif ice.level < ice.upgrade_level_limit and (best_move is "Upgrade" or best_move is None):
                if ices[ice].extra > 0 and ice.get_turns_till_arrival(game.get_cloneberg()) < min([ice.get_turns_till_arrival(enemy) for enemy in game.get_enemy_icebergs()]):
                    turns = ice.get_turns_till_arrival(game.get_cloneberg()) * 2 + game.cloneberg_max_pause_turns
                    turns_till_upgrade = ices[ice].get_turns_till_upgrade()

                    if turns_till_upgrade > turns:  # TODO - optimize this
                        ices[ice].action = ("Upgrade",)
                    else:
                        ices[ice].action = ("Clone", ices[ice].extra, turns)
                else:
                    ices[ice].action = ("Upgrade",)
            elif ice.level == ice.upgrade_level_limit:
                turns = ice.get_turns_till_arrival(game.get_cloneberg()) * 2 + game.cloneberg_max_pause_turns
                ices[ice].action = ("Clone", ices[ice], turns)

    # Synchronize cooperate attackers decision
    for ice in game.get_my_icebergs():
        if len(ices[ice].cooperate) > 0:
            if any([ices[friend].action[0] is not None and ices[friend].action[0] is not "Send" for friend in game.get_my_icebergs()]):
                ices[ice].action = ("Upgrade",)

    # Execute actions for Ices
    for ice in game.get_my_icebergs():
        if ices[ice].action is not None:
            action = ices[ice].action

            if action[0] == "Upgrade" and ices[ice].extra >= ice.upgrade_cost:
                if ices[ice].calculate_different_changes(game.get_myself(), [(game.get_enemy_icebergs()[0], ice.upgrade_cost, 1)])[0]:
                    ice.upgrade()
                    ices[ice].extra = 0
            elif action[0] == "Send":
                if ices[ice].extra >= action[2]:
                    ice.send_penguins(action[1], int(action[2]))
                    ices[ice].extra -= action[2]

            if action[0] == "Send" or action[0] == "Clone":
                if ices[ice].extra > 0 and ice.get_turns_till_arrival(game.get_cloneberg()) < min([ice.get_turns_till_arrival(enemy) for enemy in game.get_enemy_icebergs()]):  # TODO - optimize this
                    ice.send_penguins(game.get_cloneberg(), int(ices[ice].extra))

# TODO - better clone system
# TODO - proper calculation of danger, also in future (for cap especially)
# TODO - calculate danger of penguin speed up
# TODO - when is danger too scared?
# TODO - not updating enough - maybe bad, maybe good and looks bad to human eye
# TODO - improper cap danger calculations
# TODO - speed up for clone? if on their way to clone and can reclone at a more efficient rate with acceleration
# TODO - don't attack enemy if can be recaptured quickly
# TODO - what about implementing my own strategy to find danger?
# TODO - inoptimal strategies: maxing out the level of one iceberg and him helping the others out; always attacking cap with one more than it has; condensing all penguins and quick attack on cap
# TODO - upgrading for saftey?
# TODO - don't cancel attack when cooperate
# TODO - calculate efficient route - upgrade, clone, or attack
# TODO - make icebergs value upgrades more than sending, unless it's saving
# TODO - dont attack neutral if enemy is closer to it, attack neutral and enemies seperatley
