// 목표가 바뀌어도 밝기와 변화 속도를 유지하는 임계 감쇠 전환.
class ChargeTransition {
  value = 0;
  velocity = 0;
  target = 0;
  setActive(active) { this.target = active ? 1 : 0; }
  update(dt) {
    if (!Number.isFinite(dt) || dt < 0) throw new RangeError('유효한 경과 시간이 필요합니다.');
    if (dt === 0) return;
    const w = this.target ? 18 : 14, e = this.value - this.target;
    const c = this.velocity + w * e, decay = Math.exp(-w * dt);
    this.value = this.target + (e + c * dt) * decay;
    this.velocity = (this.velocity - w * c * dt) * decay;
    if (this.value < 0 || this.value > 1) {
      this.value = Math.max(0, Math.min(1, this.value)); this.velocity = 0;
    }
    if (Math.abs(this.value - this.target) < .00005 && Math.abs(this.velocity) < .001) {
      this.value = this.target; this.velocity = 0;
    }
  }
}
globalThis.ChargeTransition = ChargeTransition;
