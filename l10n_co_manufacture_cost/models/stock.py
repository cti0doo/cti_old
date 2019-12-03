# -*- coding: utf-8 -*-
from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _run_fifo(self, move, quantity=None):
        move.ensure_one()
        # Find back incoming stock moves (called candidates here) to value this move.
        valued_move_lines = move.move_line_ids.filtered(
            lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued())
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                 move.product_id.uom_id)

        qty_to_take_on_candidates = quantity or valued_quantity
        candidates = move.product_id._get_fifo_candidates_in_move(move.location_id)
        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        for candidate in candidates:
            new_standard_price = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates

            # As applying a landed cost do not update the unit price, naivelly doing
            # something like qty_taken_on_candidate * candidate.price_unit won't make
            # the additional value brought by the landed cost go away.
            candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
            value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
            candidate_vals = {
                'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                'remaining_value': candidate.remaining_value - value_taken_on_candidate,
            }
            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            if qty_to_take_on_candidates == 0:
                break

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.standard_price = new_standard_price

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        if qty_to_take_on_candidates == 0:
            move.write({
                'value': -tmp_value if not quantity else move.value or -tmp_value,
                # outgoing move are valued negatively
                'price_unit': -tmp_value / move.product_qty,
            })
        elif qty_to_take_on_candidates > 0:
            last_fifo_price = new_standard_price or move.product_id.standard_price
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            vals = {
                'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
                'remaining_value': move.remaining_value + negative_stock_value,
                'value': -tmp_value + negative_stock_value,
                'price_unit': (-tmp_value + negative_stock_value) / (move.product_qty or quantity),
            }
            move.write(vals)
        return tmp_value


class ProductCandidates(models.Model):
    _inherit = "product.product"

    def _get_fifo_candidates_in_move(self, location_id):
        """ Find IN moves that can be used to value OUT moves.
        """
        self.ensure_one()
        domain = [('product_id', '=', self.id), ('remaining_qty', '>', 0.0), ('location_dest_id', '=', location_id.id)] + \
                 self.env[
                     'stock.move']._get_in_base_domain()
        candidates = self.env['stock.move'].search(domain, order='date, id')
        return candidates
