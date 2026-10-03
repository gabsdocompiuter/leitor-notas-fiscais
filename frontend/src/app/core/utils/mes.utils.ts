export function formatarMes(data: Date): string {
  return `${String(data.getFullYear()).padStart(4, '0')}-${String(data.getMonth() + 1).padStart(2, '0')}`;
}

export function deslocarMes(mes: string, quantidade: number): string {
  const data = new Date(`${mes}-01T12:00:00`);
  data.setMonth(data.getMonth() + quantidade);
  return formatarMes(data);
}

export function mesValido(mes: string): boolean {
  return (
    /^\d{4}-(0[1-9]|1[0-2])$/.test(mes) &&
    Number(mes.slice(0, 4)) >= 2 &&
    Number(mes.slice(0, 4)) <= 9998
  );
}
