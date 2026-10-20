export function createRepository(pool) {
  async function transaction(work) {
    const connection = await pool.getConnection();
    try {
      await connection.beginTransaction();
      const result = await work(connection);
      await connection.commit();
      return result;
    } catch (error) { await connection.rollback(); throw error; }
    finally { connection.release(); }
  }
  return {
    async findUser(usuario) {
      const [rows] = await pool.execute('SELECT id, usuario, contrasena, email, full_name FROM usuarios WHERE usuario = ? LIMIT 1', [usuario]);
      return rows[0];
    },
    async user(id) {
      const [rows] = await pool.execute('SELECT id, usuario, email, full_name FROM usuarios WHERE id = ?', [id]);
      return rows[0];
    },
    async register(data, hash) {
      // Legacy usuarios has no unique index: named lock serializes API registrations.
      const connection = await pool.getConnection();
      let locked = false;
      try {
        const [[lock]] = await connection.query("SELECT GET_LOCK('aimharder-api-register', 10) AS acquired");
        locked = Number(lock.acquired) === 1;
        if (!locked) throw Object.assign(new Error('Registro ocupado. Reintenta.'), { status: 503 });
        await connection.beginTransaction();
        const [existing] = await connection.execute('SELECT id FROM usuarios WHERE usuario = ? LIMIT 1', [data.usuario]);
        if (existing.length) throw Object.assign(new Error('El usuario ya existe'), { status: 409 });
        const [result] = await connection.execute('INSERT INTO usuarios (usuario, contrasena, email, full_name) VALUES (?, ?, ?, ?)', [data.usuario, hash, data.email, data.full_name]);
        await connection.execute("INSERT INTO configs (user_id, aimharder_user, aimharder_pass, periodicidad, tipo_app, gym) VALUES (?, '', '', 'daily', 'aimharder', '')", [result.insertId]);
        await connection.commit();
      } catch (error) { await connection.rollback(); throw error; }
      finally {
        try { if (locked) await connection.query("SELECT RELEASE_LOCK('aimharder-api-register')"); }
        finally { connection.release(); }
      }
    },
    async dashboard(id, usuario) {
      const [[configs], [bookings], [classes], [hours]] = await Promise.all([
        pool.execute('SELECT gym, periodicidad, tipo_app, aimharder_user, (COALESCE(aimharder_pass, \'\') <> \'\') AS has_password FROM configs WHERE user_id = ?', [id]),
        pool.execute('SELECT dia, hora, clase, activo FROM bookings WHERE user_id = ?', [id]),
        pool.execute('SELECT class_name FROM current_classes WHERE user_id = ? AND usuario = ? ORDER BY class_name', [id, usuario]),
        pool.execute('SELECT hora FROM current_hours WHERE user_id = ? AND usuario = ? ORDER BY hora', [id, usuario]),
      ]);
      return { config: configs[0] || { gym: '', periodicidad: 'daily', tipo_app: 'aimharder', aimharder_user: '', has_password: 0 },
        bookings: bookings.map(row => ({ ...row, activo: Boolean(row.activo) })),
        classes: classes.map(row => row.class_name), hours: hours.map(row => row.hora) };
    },
    async saveConfig(id, config) {
      return transaction(async connection => {
        // Lock the owner even when configs does not exist yet.
        await connection.execute('SELECT id FROM usuarios WHERE id = ? FOR UPDATE', [id]);
        const [[old]] = await connection.execute('SELECT aimharder_pass FROM configs WHERE user_id = ?', [id]);
        const password = config.aimharder_pass ?? old?.aimharder_pass;
        if (!password) throw Object.assign(new Error('Introduce contraseña del proveedor'), { status: 400 });
        await connection.execute(`INSERT INTO configs (user_id, gym, periodicidad, tipo_app, aimharder_user, aimharder_pass)
          VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE gym=VALUES(gym), periodicidad=VALUES(periodicidad),
          tipo_app=VALUES(tipo_app), aimharder_user=VALUES(aimharder_user), aimharder_pass=VALUES(aimharder_pass)`,
        [id, config.gym, config.periodicidad, config.tipo_app, config.aimharder_user, password]);
      });
    },
    async saveBookings(id, rows) {
      return transaction(async connection => {
        await connection.execute('SELECT id FROM usuarios WHERE id = ? FOR UPDATE', [id]);
        for (const row of rows) {
          await connection.execute(`INSERT INTO bookings (user_id, dia, hora, clase, activo) VALUES (?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE hora=VALUES(hora), clase=VALUES(clase), activo=VALUES(activo),
            fecha_evento=CASE WHEN VALUES(hora) <> '' THEN TIMESTAMP(DATE(COALESCE(fecha_evento, NOW())), LEFT(VALUES(hora), 5)) ELSE fecha_evento END`,
          [id, row.dia, row.hora, row.clase, row.activo]);
        }
      });
    },
  };
}
