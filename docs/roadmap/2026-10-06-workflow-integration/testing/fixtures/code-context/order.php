<?php
declare(strict_types=1);

final class OrderService
{
    public function total(array $prices): int
    {
        return array_sum($prices);
    }
}
