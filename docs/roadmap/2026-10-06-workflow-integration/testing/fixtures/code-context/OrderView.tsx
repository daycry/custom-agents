export function formatTotal(total: number): string {
  return `${total} EUR`;
}

export function OrderView({ total }: { total: number }) {
  return <output aria-label="Order total">{formatTotal(total)}</output>;
}
